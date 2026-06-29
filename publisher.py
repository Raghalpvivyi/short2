# -*- coding: utf-8 -*-
"""
موديول النشر التلقائي والجدولة لإنستغرام وتيك توك
يتضمن استخدام الـ APIs الرسمية للشبكات الاجتماعية لرفع الفيديوهات وجدولتها.
"""

import os
import time
import requests
from dotenv import load_dotenv

# تحميل المتغيرات البيئية
load_dotenv()

class SocialPublisher:
    def __init__(self):
        # إعدادات إنستغرام (Meta Graph API)
        self.ig_access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.ig_account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
        
        # إعدادات تيك توك
        self.tt_access_token = os.getenv("TIKTOK_ACCESS_TOKEN")
        self.tt_open_id = os.getenv("TIKTOK_OPEN_ID")

    def publish_to_instagram(self, video_url, caption):
        """
        رفع ونشر ريلز (Reels) على حساب إنستغرام لقطاع الأعمال (Instagram Business Account)
        تتطلب هذه العملية خطوتين بحسب Meta API:
        1. إنشاء حاوية وسائط (Media Container) للفيديو.
        2. نشر الحاوية بعد معالجتها بنجاح.
        """
        if not self.ig_access_token or not self.ig_account_id:
            print("[خطأ إنستغرام] ينقصك INSTAGRAM_ACCESS_TOKEN أو INSTAGRAM_BUSINESS_ACCOUNT_ID في ملف الإعدادات.")
            return False

        print("[إنستغرام] 1/3 البدء بإنشاء حاوية الوسائط (Media Container)...")
        # رابط Meta API
        url = f"https://graph.facebook.com/v17.0/{self.ig_account_id}/media"
        
        payload = {
            "media_type": "REELS",
            "video_url": video_url, # يجب أن يكون رابط الفيديو عاماً وقابلاً للتحميل بواسطة خوادم فيسبوك
            "caption": caption,
            "access_token": self.ig_access_token
        }

        try:
            # الخطوة الأولى: طلب رفع الفيديو
            response = requests.post(url, data=payload)
            response.raise_for_status()
            creation_id = response.json().get("id")
            print(f"[إنستغرام] تم إنشاء حاوية بنجاح، كود العملية (Creation ID): {creation_id}")

            # الخطوة الثانية: التحقق من اكتمال المعالجة (التحقق الدوري)
            # بما أن معالجة الفيديو في فيسبوك تستغرق وقتاً، سنفحص الحالة كل 10 ثوانٍ
            status_url = f"https://graph.facebook.com/v17.0/{creation_id}"
            params = {
                "fields": "status_code",
                "access_token": self.ig_access_token
            }
            
            print("[إنستغرام] 2/3 جاري فحص حالة معالجة الفيديو بانتظار الانتهاء...")
            max_attempts = 15
            for attempt in range(max_attempts):
                time.sleep(15) # الانتظار قبل كل فحص
                status_res = requests.get(status_url, params=params)
                status_res.raise_for_status()
                status_code = status_res.json().get("status_code")
                
                print(f" - محاولة فحص الحالة ({attempt+1}/{max_attempts}): {status_code}")
                if status_code == "FINISHED":
                    print("[إنستغرام] ممتاز! اكتملت معالجة الفيديو وأصبح جاهزاً للنشر.")
                    break
                elif status_code == "ERROR":
                    raise Exception("فشلت معالجة الفيديو على خوادم إنستغرام.")
            else:
                raise TimeoutError("استغرقت معالجة الفيديو وقتاً طويلاً على خوادم إنستغرام.")

            # الخطوة الثالثة: نشر الحاوية (Publish Media Container)
            print("[إنستغرام] 3/3 جاري إرسال طلب النشر الفعلي...")
            publish_url = f"https://graph.facebook.com/v17.0/{self.ig_account_id}/media_publish"
            publish_payload = {
                "creation_id": creation_id,
                "access_token": self.ig_access_token
            }
            
            publish_res = requests.post(publish_url, data=publish_payload)
            publish_res.raise_for_status()
            post_id = publish_res.json().get("id")
            
            print(f"[نجاح] تم نشر الفيديو بنجاح على حساب إنستغرام! كود المنشور: {post_id}")
            return True

        except Exception as e:
            print(f"[خطأ إنستغرام] فشل النشر التلقائي: {str(e)}")
            return False

    def publish_to_tiktok(self, local_video_path, caption):
        """
        رفع ونشر فيديو على منصة تيك توك باستخدام TikTok Direct Post API
        الخطوات القياسية لرفع الفيديوهات:
        1. تهيئة الرفع (Initialize Creator Upload) لطلب رابط الرفع السحابي.
        2. رفع الفيديو الفعلي كـ Binary Data إلى الرابط المستلم.
        3. تأكيد الرفع وإتمام عملية النشر.
        """
        if not self.tt_access_token:
            print("[خطأ تيك توك] ينقصك TIKTOK_ACCESS_TOKEN في ملف الإعدادات.")
            return False

        print("[تيك توك] 1/3 جاري إرسال طلب تهيئة رفع الفيديو...")
        init_url = "https://open.tiktokapis.com/v2/post/publish/video/init/"
        
        headers = {
            "Authorization": f"Bearer {self.tt_access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }
        
        # حجم الفيديو بالبايت
        video_size = os.path.getsize(local_video_path)
        
        payload = {
            "post_info": {
                "title": caption[:150],  # حد تيك توك للعنوان
                "privacy_level": "PUBLIC_TO_EVERYONE",
                "allow_comment": True,
                "allow_duet": True,
                "allow_stitch": True
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": video_size, # نرفع الملف كقطعة واحدة لسهولة السكربت
                "total_chunk_count": 1
            }
        }

        try:
            response = requests.post(init_url, json=payload, headers=headers)
            response.raise_for_status()
            res_data = response.json().get("data", {})
            upload_url = res_data.get("upload_url")
            publish_id = res_data.get("publish_id")
            
            if not upload_url:
                raise ValueError("لم يرجع تيك توك رابط الرفع المطلوب.")

            # الخطوة الثانية: رفع الفيديو الثنائي (Binary Upload)
            print("[تيك توك] 2/3 جاري رفع ملف الفيديو ثنائي الأبعاد...")
            upload_headers = {
                "Content-Type": "video/mp4",
                "Content-Length": str(video_size)
            }
            
            with open(local_video_path, "rb") as video_file:
                upload_res = requests.put(upload_url, data=video_file, headers=upload_headers)
                upload_res.raise_for_status()
                
            print("[تيك توك] تم رفع الملف بنجاح.")

            # الخطوة الثالثة: المنشور يتم معالجته وجدولته تلقائياً على تيك توك
            # يتم فحص حالة النشر باستخدام publish_id إذا دعت الحاجة
            print(f"[نجاح] تم إتمام النشر على تيك توك بنجاح! كود النشر: {publish_id}")
            return True

        except Exception as e:
            print(f"[خطأ تيك توك] فشلت عملية النشر التلقائي: {str(e)}")
            return False

if __name__ == "__main__":
    # يمكن كتابة كود اختبار تجريبي هنا
    publisher = SocialPublisher()
