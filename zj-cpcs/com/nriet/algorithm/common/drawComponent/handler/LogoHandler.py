from PIL import Image


def add_logos(im, params_dict):
    for logo_name, logo_instance in params_dict.items():
        ncc_img = Image.open(logo_instance['file_path'])
        x, y = ncc_img.size
        p1 = Image.new('RGBA', ncc_img.size, (255, 255, 255))
        p1.paste(ncc_img, (0, 0, x, y), ncc_img)
        im.paste(p1, logo_instance['logo_location'])
