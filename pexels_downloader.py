# -*- coding: utf-8 -*-
"""
موديول تحميل الفيديوهات من Pexels API
هذا الملف مسؤول عن البحث والتحميل التلقائي للفيديوهات العمودية بجودة عالية.
"""

import os
import requests
import random
from dotenv import load_dotenv

# تحميل المتغيرات البيئية
load_dotenv()

class PexelsDownloader:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("PEXELS_API_KEY")
        self.base_url = "https://api.pexels.com/videos"
        
        if not self.api_key:
            print("[تحذير] لم يتم العثور على مفتاح PEXELS_API_KEY في البيئة.")

    def search_videos(self, query, min_width=1080, min_height=1920, limit=5):
        """
        البحث عن فيديوهات عمودية تناسب Reels/TikTok بناءً على كلمة مفتاحية
        """
        if not self.api_key:
            raise ValueError("مفتاح Pexels API مطلوب لإجراء عملية البحث.")

        headers = {
            "Authorization": self.api_key
        }
        
        # نطلب وضعية عمودية (portrait) وفيديوهات تناسب جودة جيدة
        params = {
            "query": query,
            "orientation": "portrait",
            "per_page": limit,
            "size": "medium"  # للتوفير في حجم التحميل وسرعة المعالجة
        }

        try:
            print(f"[Pexels] جاري البحث عن فيديوهات للوسم: '{query}'...")
            response = requests.get(f"{self.base_url}/search", headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            videos = data.get("videos", [])
            
            if not videos:
                print(f"[Pexels] لم يتم العثور على فيديوهات تطابق البحث: '{query}'")
                return []
                
            processed_videos = []
            for video in videos:
                # تصفية روابط تحميل الفيديو واختيار الجودة الأنسب (HD)
                video_files = video.get("video_files", [])
                
                # نفضل صيغة mp4 وجودة HD (أقرب ما يكون لـ 1080x1920 أو 720x1280)
                suitable_file = None
                for vf in video_files:
                    if vf.get("file_type") == "video/mp4":
                        width = vf.get("width", 0)
                        height = vf.get("height", 0)
                        # تفضيل الفيديوهات العمودية
                        if height > width:
                            suitable_file = vf
                            # إذا وجدنا الجودة المثالية نكتفي بها
                            if 720 <= width <= 1080:
                                break
                
                if not suitable_file and video_files:
                    # في حال عدم العثور على النسبة المثالية، نأخذ أول ملف متاح
                    suitable_file = video_files[0]
                    
                if suitable_file:
                    processed_videos.append({
                        "id": video.get("id"),
                        "url": suitable_file.get("link"),
                        "width": suitable_file.get("width"),
                        "height": suitable_file.get("height"),
                        "duration": video.get("duration"),
                        "photographer": video.get("user", {}).get("name")
                    })
            
            print(f"[Pexels] تم العثور على {len(processed_videos)} فيديو بجودة عمودية مناسبة.")
            return processed_videos

        except Exception as e:
            print(f"[خطأ Pexels] فشل البحث عن الفيديوهات: {str(e)}")
            return []

    def download_video(self, video_url, output_path):
        """
        تحميل الفيديو من الرابط المباشر وحفظه محلياً
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            print(f"[Pexels] جاري تحميل الفيديو من الرابط: {video_url[:40]}...")
            
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        
            print(f"[نجاح] تم حفظ الفيديو بنجاح في المسار: {output_path}")
            return True
        except Exception as e:
            print(f"[خطأ تحميل] فشل تحميل الفيديو: {str(e)}")
            return False

if __name__ == "__main__":
    # مثال على التشغيل الفردي للموديول
    downloader = PexelsDownloader()
    # يمكن فك التعليق لاختبار الموديول
    # videos = downloader.search_videos("cute baby")
    # if videos:
    #     downloader.download_video(videos[0]["url"], "temp/test_video.mp4")
