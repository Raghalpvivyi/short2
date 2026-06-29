# -*- coding: utf-8 -*-
"""
الملف الرئيسي للتشغيل (Orchestration Pipeline)
يقوم هذا السكربت بجمع كل الموديولات معاً: جلب الفيديو، معالجته، كتابة النصوص، ونشره تلقائياً.
"""

import os
import csv
from pexels_downloader import PexelsDownloader
from video_processor import VideoProcessor
from publisher import SocialPublisher

def run_automation_pipeline(content_list, music_file=None, pexels_query="kids playing"):
    """
    سير العمل المتكامل (Workflow Pipeline):
    1. الاتصال بـ Pexels والبحث عن الفيديوهات الخام وتحميلها.
    2. معالجة الفيديو وإضافة النص (Text Overlay) وخلفية موسيقية.
    3. النشر المباشر عبر الـ API لإنستغرام وتيك توك.
    """
    print("=" * 60)
    print("🚀 بدء أتمتة إنتاج ونشر الفيديوهات القصيرة للأطفال 🚀")
    print("=" * 60)

    # 1. تهيئة الموديولات المختلفة
    downloader = PexelsDownloader()
    processor = VideoProcessor()
    publisher = SocialPublisher()

    # إنشاء المجلدات المؤقتة ومجلد المخرجات إذا لم تكن موجودة
    os.makedirs("temp", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    # 2. البحث عن فيديوهات خام على Pexels
    raw_videos = downloader.search_videos(pexels_query, limit=len(content_list))
    
    if not raw_videos:
        print("[خطأ] تعذر العثور على أي فيديوهات خام من Pexels للبدء.")
        return False

    success_count = 0
    for idx, item in enumerate(content_list):
        print(f"\n[عنصر {idx+1}/{len(content_list)}] جاري البدء في معالجة:")
        print(f" - النص: {item.get('text')}")
        print(f" - الوصف (Caption): {item.get('caption')}")

        # تحديد ملف الفيديو الخام المخصص لهذا العنصر
        video_data = raw_videos[idx % len(raw_videos)]
        raw_video_path = f"temp/raw_{video_data['id']}.mp4"
        final_video_path = f"output/final_reel_{idx+1}.mp4"

        # تحميل الفيديو الخام من Pexels
        download_success = downloader.download_video(video_data["url"], raw_video_path)
        
        if not download_success:
            print(f"[تنبيه] تخطي هذا العنصر بسبب فشل تحميل الفيديو من Pexels.")
            continue

        # 3. معالجة الفيديو (قص، إعادة مقاس، دمج نص، إضافة موسيقى)
        processing_success = processor.process_reel(
            video_path=raw_video_path,
            text=item.get("text"),
            output_path=final_video_path,
            bg_music_path=music_file,
            bg_music_volume=0.15
        )

        if not processing_success:
            print(f"[تنبيه] تخطي هذا العنصر بسبب فشل عملية المعالجة البصرية.")
            continue

        # 4. النشر وجدولة المحتوى (إذا تم توفير بيانات الاعتماد)
        # ملاحظة: لإنستغرام، يتطلب الأمر أن يكون الفيديو النهائي مرفوعاً على رابط عام (URL)
        # لذلك سنقوم بالنشر فقط إذا كان لدينا بيئة حقيقية لرفع الفيديو (كخادم ويب مثلاً)
        caption_text = f"{item.get('caption')}\n\n{item.get('hashtags', '')}"
        
        # محاكاة أو نشر حقيقي
        print("[نشر] جاري تحضير النشر على المنصات الاجتماعية...")
        
        # تيك توك يقبل الرفع المباشر من مسار محلي
        tt_success = publisher.publish_to_tiktok(final_video_path, caption_text)
        if tt_success:
            print("[تيك توك] تم النشر بنجاح!")
        else:
            print("[تيك توك] تم حفظ الفيديو محلياً للنشر اليدوي لاحقاً.")

        # إنستغرام يتطلب رابط فيديو عام
        # سنقوم بالنشر فقط إذا تم تزويدنا برابط عام للفيديو النهائي
        public_video_url = item.get("public_video_url")
        if public_video_url:
            ig_success = publisher.publish_to_instagram(public_video_url, caption_text)
            if ig_success:
                print("[إنستغرام] تم نشر الفيديو بنجاح عبر الرابط العام!")
        else:
            print("[إنستغرام] يتطلب نشر ريلز رابطاً عاماً للفيديو. تم حفظ الفيديو محلياً في مجلد output.")

        success_count += 1
        print(f"[عنصر {idx+1}] اكتملت الأتمتة له بنجاح 🎉")

    print("\n" + "=" * 60)
    print(f"🏁 اكتمل تشغيل نظام الأتمتة بنجاح! تم إنتاج {success_count} فيديو.")
    print("=" * 60)
    return True

if __name__ == "__main__":
    # قائمة تجريبية للنصائح التربوية للأطفال
    sample_content = [
        {
            "text": "هل تعلم أن القراءة لطفلك قبل النوم يومياً تنمي ذكائه اللغوي بنسبة 40%؟ 📚👶",
            "caption": "طور لغة وذكاء طفلك بخطوة بسيطة كل ليلة!",
            "hashtags": "#تربية_أطفال #أطفال_سعداء #نصائح_تربوية #أمومة #reels #tiktok"
        },
        {
            "text": "المدح الإيجابي للأفعال وليس للطفل نفسه يبني ثقة قوية بالذات ويحفزه للمحاولة. ⭐",
            "caption": "علم طفلك كيف يثق بنفسه من خلال كلماتك الذكية.",
            "hashtags": "#ثقة_النفس #تربية_بذكاء #أطفال #تطوير_الطفل #قصص_اطفال"
        }
    ]
    
    # تشغيل خط الأتمتة
    # run_automation_pipeline(sample_content, music_file="assets/lullaby.mp3", pexels_query="cute baby")
