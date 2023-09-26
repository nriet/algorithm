from PIL import Image, ImageFont, ImageDraw


def setting_font(dataSources1, image_path, mainTitle, subTitles, unit):
    font = ImageFont.truetype("/home/xulh/mnt/python/python_script/orl/font/msyh.ttc", 30)
    font1 = ImageFont.truetype("/home/xulh/mnt/python/python_script/orl/font/msyh.ttc", 20)
    font2 = ImageFont.truetype("/home/xulh/mnt/python/python_script/orl/font/msyh.ttc", 15)
    im = Image.open(image_path + ".png", "r")
    draw = ImageDraw.Draw(im)
    ont_width, font_height = draw.textsize(mainTitle, font)
    ont_width1, font_height1 = draw.textsize(subTitles, font1)
    ont_width2, font_height2 = draw.textsize(dataSources1, font2)
    ont_width3, font_height3 = draw.textsize(unit, font2)
    draw.text(((930 - ont_width) / 2, 150), mainTitle, font=font, fill=(0, 0, 0, 0))
    draw.text(((930 - ont_width1) / 2, 200), subTitles, font=font1, fill=(0, 0, 0, 0))
    draw.text((900 - ont_width2, 150), dataSources1, font=font2, fill=(0, 0, 0, 0))
    draw.text((900 - ont_width3, 200), unit, font=font2, fill=(0, 0, 0, 0))
    return im
