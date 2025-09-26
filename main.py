import os
import sys
import argparse
from PIL import Image, ImageDraw, ImageFont, ExifTags
from datetime import datetime
import glob


def get_exif_datetime(image_path):
    try:
        with Image.open(image_path) as img:
            exif_data = img._getexif()
            if exif_data:
                # 查找拍摄时间的EXIF标签
                for tag_id, value in exif_data.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    if tag == 'DateTimeOriginal':
                        # 转换时间格式：2023:10:15 12:30:45 -> 2023年10月15日
                        if value:
                            dt = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                            return f"{dt.year}\\{dt.month}\\{dt.day}"
            return None
    except Exception as e:
        print(f"读取 {image_path} 的EXIF信息失败: {e}")
        return None


def get_position(img_width, img_height, text_width, text_height, position):
    padding = 20  # 边距

    if position == "top-left":
        return (padding, padding)
    elif position == "top-right":
        return (img_width - text_width - padding, padding)
    elif position == "bottom-left":
        return (padding, img_height - text_height - padding)
    elif position == "bottom-right":
        return (img_width - text_width - padding, img_height - text_height - padding)
    elif position == "center":
        return ((img_width - text_width) // 2, (img_height - text_height) // 2)
    elif position == "top-center":
        return ((img_width - text_width) // 2, padding)
    elif position == "bottom-center":
        return ((img_width - text_width) // 2, img_height - text_height - padding)
    else:
        # 默认右下角
        return (img_width - text_width - padding, img_height - text_height - padding)


def add_watermark(image_path, output_path, font_size=36, color='white', position='bottom-right'):
    try:
        # 读取图片
        with Image.open(image_path) as img:
            # 转换RGBA模式以便处理透明度
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            # 创建绘图对象
            draw = ImageDraw.Draw(img)

            # 获取水印文本
            watermark_text = get_exif_datetime(image_path)
            if not watermark_text:
                watermark_text = datetime.now().strftime("%Y年%m月%d日")
                print(f"水印: {watermark_text}")

            # 加载字体（使用默认字体）
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
                except:
                    try:
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
                    except:
                        font = ImageFont.load_default()
                        print("使用默认字体")

            # 计算文本尺寸
            bbox = draw.textbbox((0, 0), watermark_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # 计算位置
            x, y = get_position(img.width, img.height, text_width, text_height, position)

            # 添加文本阴影效果（可选）
            shadow_color = 'black' if color == 'white' else 'black'
            draw.text((x + 2, y + 2), watermark_text, font=font, fill=shadow_color)

            # 添加主文本
            draw.text((x, y), watermark_text, font=font, fill=color)

            # 保存图片
            if img.mode == 'RGBA':
                img = img.convert('RGB')

            img.save(output_path, quality=95)
            print(f"已保存: {output_path}")

    except Exception as e:
        print(f"处理图片 {image_path} 时出错: {e}")


def main():
    parser = argparse.ArgumentParser(description='图片水印添加工具')
    parser.add_argument('image_path', help='图片文件路径或目录路径')
    parser.add_argument('--font-size', type=int, default=36, help='字体大小（默认：36）')
    parser.add_argument('--color', default='white', help='字体颜色（默认：white）')
    parser.add_argument('--position', default='bottom-right',
                        choices=['top-left', 'top-center', 'top-right',
                                 'center', 'bottom-left', 'bottom-center', 'bottom-right'],
                        help='水印位置（默认：bottom-right）')

    args = parser.parse_args()

    # 检查输入路径是否存在
    if not os.path.exists(args.image_path):
        print(f"错误：路径 {args.image_path} 不存在")
        sys.exit(1)

    # 确定输入是文件还是目录
    if os.path.isfile(args.image_path):
        image_files = [args.image_path]
        input_dir = os.path.dirname(args.image_path) or '.'
    else:
        input_dir = args.image_path
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.webp']
        image_files = []
        for ext in image_extensions:
            image_files.extend(glob.glob(os.path.join(input_dir, ext)))
            image_files.extend(glob.glob(os.path.join(input_dir, ext.upper())))

    if not image_files:
        print(f"在 {args.image_path} 中未找到图片文件")
        sys.exit(1)

    # 创建输出目录
    output_dir = os.path.join(input_dir, f"{os.path.basename(input_dir)}_watermark")
    os.makedirs(output_dir, exist_ok=True)

    print(f"找到 {len(image_files)} 张图片")
    print(f"输出目录: {output_dir}")
    print(f"字体大小: {args.font_size}, 颜色: {args.color}, 位置: {args.position}")
    print("-" * 50)

    # 处理每张图片
    success_count = 0
    for image_path in image_files:
        try:
            filename = os.path.basename(image_path)
            output_path = os.path.join(output_dir, filename)

            print(f"处理: {filename}")
            add_watermark(image_path, output_path, args.font_size, args.color, args.position)
            success_count += 1

        except Exception as e:
            print(f"处理 {image_path} 失败: {e}")

    print("-" * 50)
    print(f"处理完成！成功处理 {success_count}/{len(image_files)} 张图片")


if __name__ == "__main__":
    main()