from PIL import Image, ImageDraw

def create_icon():
    img = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Draw a blue background circle
    d.ellipse((2, 2, 62, 62), fill=(41, 128, 185))
    # Draw some white text "K"
    d.text((22, 16), "K", fill=(255, 255, 255), font=None)
    
    img.save('icon.png')
    img.save('icon.ico', format='ICO')

if __name__ == "__main__":
    create_icon()
