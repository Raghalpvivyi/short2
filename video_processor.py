# -*- coding: utf-8 -*-
"""
موديول معالجة الفيديوهات وإضافة المؤثرات البصرية والصوتية
باستخدام مكتبة MoviePy لإعداد فيديوهات بمقاس 1080x1920 جاهزة للنشر.
"""

import os
import sys
from dotenv import load_dotenv

# تحميل المتغيرات البيئية
load_dotenv()

try:
    # مكتبة moviepy لمعالجة الفيديوهات
    from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, CompositeAudioClip
    from moviepy.audio.fx.all import volumex
except ImportError:
    print("[ملاحظة] مكتبة MoviePy غير مثبتة في هذه البيئة. يرجى تثبيتها عبر: pip install moviepy")

class VideoProcessor:
    def __init__(self):
        # التأكد من تهيئة مسار خطوط مخصصة إن دعت الحاجة
        self.default_font = os.getenv("VIDEO_FONT", "Arial")
        self.target_size = (1080, 1920) # أبعاد ريلز وتيك توك القياسية

    def process_reel(self, video_path, text, output_path, bg_music_path=None, bg_music_volume=0.15):
        """
        دمج النص والموسيقى مع الفيديو الخام لإنتاج الفيديو النهائي.
        """
        print(f"[معالجة] بدء معالجة الفيديو: {video_path}")
        print(f"[معالجة] محتوى النص المضاف: '{text[:30]}...'")
        
        try:
            # 1. تحميل الفيديو الأصلي
            clip = VideoFileClip(video_path)
            
            # 2. تغيير المقاس والقص ليناسب 1080x1920 (9:16) عمودياً
            # إذا كان الفيديو بالفعل عمودياً نقوم فقط بضبط أبعاده
            w, h = clip.size
            ratio = 1080 / 1920
            
            if abs((w / h) - ratio) > 0.05:
                print("[معالجة] جاري تعديل أبعاد الفيديو الخام ليطابق نسبة 9:16...")
                # نقوم بقص الفيديو من المنتصف ليتوافق مع العرض والارتفاع المستهدف
                target_w = int(h * ratio)
                if target_w <= w:
                    clip = clip.crop(x_center=w/2, width=target_w, height=h)
                else:
                    target_h = int(w / ratio)
                    clip = clip.crop(y_center=h/2, width=w, height=target_h)
            
            # إعادة تحجيم الفيديو ليكون بدقة 1080x1920 بالضبط
            clip = clip.resize(self.target_size)
            
            # قصر مدة الفيديو إذا كان طويلاً جداً (مثلاً 15 ثانية مناسبة جداً لـ Reels)
            duration = min(clip.duration, 15.0)
            clip = clip.subclip(0, duration)

            # 3. إنشاء النص المتداخل (Text Overlay)
            # نقوم بتقسيم النص لأسطر قصيرة تلقائياً لضمان عدم خروجه من الشاشة
            wrapped_text = self._wrap_text(text, max_chars=30)
            
            # إنشاء بطاقة نصية خلفية شبه شفافة لتسهيل القراءة
            # ملاحظة: يتطلب هذا تثبيت ImageMagick على الجهاز لتشغيل TextClip في MoviePy
            try:
                text_clip = TextClip(
                    wrapped_text,
                    fontsize=50,
                    color='white',
                    font=self.default_font,
                    method='caption',
                    align='Center',
                    size=(900, None)  # عرض محدد لتغليف النص وهامش جانبي
                )
                
                # وضع خلفية داكنة خفيفة للنص لسهولة القراءة
                text_bg = TextClip(
                    " ",
                    size=(950, text_clip.h + 60),
                    bg_color='black',
                    color='black'
                ).set_opacity(0.6)
                
                # دمج النص مع خلفيته المظلمة
                text_group = CompositeVideoClip([
                    text_bg.set_position("center"),
                    text_clip.set_position("center")
                ], size=(950, text_clip.h + 80)).set_duration(duration)
                
                # تحديد موضع مجموعة النص في منتصف الشاشة عمودياً
                text_group = text_group.set_position(("center", "center"))
                
                # دمج العناصر بصرية
                final_visual_clip = CompositeVideoClip([clip, text_group])
            except Exception as e_text:
                print(f"[تحذير] فشل استخدام TextClip (قد يكون ImageMagick غير مثبت): {str(e_text)}")
                print("[تنبيه] سيتم تصدير الفيديو الأصلي بدون دمج نص لتجنب إيقاف السكربت.")
                final_visual_clip = clip

            # 4. دمج الصوت والموسيقى الخلفية
            if bg_music_path and os.path.exists(bg_music_path):
                print(f"[صوت] جاري دمج الموسيقى الخلفية من المسار: {bg_music_path}")
                music_clip = AudioFileClip(bg_music_path)
                
                # تقليص مدة الموسيقى لتطابق مدة الفيديو وتكرارها إذا لزم الأمر
                if music_clip.duration < duration:
                    # تكرار الموسيقى
                    music_clip = music_clip.loop(duration=duration)
                else:
                    music_clip = music_clip.subclip(0, duration)
                
                # خفض مستوى صوت الخلفية الموسيقية
                music_clip = music_clip.volumex(bg_music_volume)
                
                # دمج الأصوات (إذا كان للفيديو صوت أصلي نقوم بدمجهما معاً)
                if clip.audio:
                    original_audio = clip.audio.volumex(1.0) # الحفاظ على صوت الضحكات/اللعب الأصلي
                    combined_audio = CompositeAudioClip([original_audio, music_clip])
                else:
                    combined_audio = music_clip
                    
                final_visual_clip = final_visual_clip.set_audio(combined_audio)
            
            # 5. تصدير الفيديو النهائي بجودة عالية مناسبة للمنصات
            print(f"[تصدير] جاري إنتاج وتصدير الفيديو النهائي إلى: {output_path}...")
            final_visual_clip.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                fps=30,
                threads=4,
                preset="medium",
                logger=None # كتم مخرجات التيرمينال الكثيفة لـ MoviePy
            )
            
            # إغلاق الملفات لتحرير الذاكرة
            clip.close()
            final_visual_clip.close()
            print(f"[نجاح] تم إنتاج فيديو الريل بنجاح وحفظه في: {output_path}")
            return True

        except Exception as e:
            print(f"[خطأ معالجة] فشل إنتاج الفيديو النهائي: {str(e)}")
            return False

    def _wrap_text(self, text, max_chars=30):
        """
        تقسيم النص لأسطر بحد أقصى للحروف لكل سطر، للحفاظ على الجمالية والوضوح.
        """
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            # إضافة طول الكلمة ومسافة
            if current_length + len(word) + 1 <= max_chars:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_length = len(word)
                
        if current_line:
            lines.append(" ".join(current_line))
            
        return "\n".join(lines)

if __name__ == "__main__":
    # مثال على التشغيل
    processor = VideoProcessor()
    # يمكن فك التعليق للاختبار محلياً
    # processor.process_reel("temp/raw_video.mp4", "هل تعلم أن نوم الرضيع الكافي يساعد في تطوره العقلي السريع؟ 👶💡", "output/final_reel.mp4")
