import struct
import snappy
import torch
from torchvision.transforms import functional as TF
from PIL import Image
import numpy as np
import io

# TODO: delete this and rework it with zstd instead.


def save_image_snappy(x, filename):
    with open(filename, "wb") as f:
        if isinstance(x, Image.Image):
            x = TF.to_tensor(x).mul_(255).byte()
        elif isinstance(x, (torch.FloatTensor, torch.cuda.FloatTensor)):
            x = x.mul(255).byte()  # expect: float tensor
        elif isinstance(x, (torch.ByteTensor, torch.cuda.ByteTensor)):
            pass
        else:
            raise ValueError("Unknown input format")
        header = struct.pack("!LLL", x.shape[0], x.shape[1], x.shape[2])
        image_data = snappy.compress(x.numpy())
        f.write(header)
        f.write(image_data)


def load_image_snappy(filename, dtype=torch.FloatTensor):
    with open(filename, "rb") as f:
        header = f.read(3 * 4)
        image_data = f.read()
        s1, s2, s3 = struct.unpack("!LLL", header)
        x = torch.ByteTensor(np.frombuffer(snappy.decompress(image_data), dtype=np.uint8)).reshape(s1, s2, s3)
        if dtype is Image.Image:
            return TF.to_pil_image(x)
        elif dtype is torch.FloatTensor:
            return x.float().div_(255)
        elif dtype is torch.ByteTensor:
            return x
        else:
            raise ValueError("Unknown dtype")


def encode_image_snappy(x):
    with io.BytesIO() as f:
        if isinstance(x, Image.Image):
            x = TF.to_tensor(x).mul_(255).byte()
        elif isinstance(x, (torch.FloatTensor, torch.cuda.FloatTensor)):
            x = x.mul(255).byte()  # expect: float tensor
        elif isinstance(x, (torch.ByteTensor, torch.cuda.ByteTensor)):
            pass
        else:
            raise ValueError("Unknown input format")
        header = struct.pack("!LLL", x.shape[0], x.shape[1], x.shape[2])
        image_data = snappy.compress(x.numpy())
        f.write(header)
        f.write(image_data)
        return f.getvalue()


def decode_image_snappy(buf, dtype=torch.FloatTensor):
    with io.BytesIO(buf) as f:
        header = f.read(3 * 4)
        image_data = f.read()
        s1, s2, s3 = struct.unpack("!LLL", header)
        x = torch.ByteTensor(np.frombuffer(snappy.decompress(image_data), dtype=np.uint8)).reshape(s1, s2, s3)
        if dtype is Image.Image:
            return TF.to_pil_image(x)
        elif dtype is torch.FloatTensor:
            return x.float().div_(255)
        elif dtype is torch.ByteTensor:
            return x
        else:
            raise ValueError("Unknown dtype")


"""
if __name__ == "__main__":
    import time

    def save_image_fast(im, filename):
        im.save(filename, compress_level=1)

    def save_image_pth(im, filename):
        x = TF.to_tensor(im).mul_(255).byte()
        torch.save(x, filename)

    src = "tmp/miku_CC_BY-NC.jpg"
    im = load_image_rgb(src)
    buf = encode_image_snappy(im)
    im = decode_image_snappy(buf, Image.Image)

    save_image_fast(im, "tmp/miku_fast.png")
    save_image_pth(im, "tmp/miku_fast.pth")
    save_image_snappy(im, "tmp/miku_fast.sz")

    # im = load_image_snappy("tmp/miku_fast.sz", dtype=Image.Image)
    # im.show()
    N = 3000

    t = time.time()
    for _ in range(N):
        a = load_image_snappy("tmp/miku_fast.sz", dtype=torch.FloatTensor)
    print(f"save_image_snappy: {time.time() - t}")

    t = time.time()
    for _ in range(N):
        a = load_image_rgb(src)
    print(f"save_image: {time.time() - t}")

    t = time.time()
    for _ in range(N):
        a = load_image_rgb("tmp/miku_fast.png")
    print(f"save_image_fast: {time.time() - t}")

    t = time.time()
    for _ in range(N):
        a = torch.load("tmp/miku_fast.pth").float().mul_(255)
    print(f"save_image_pth: {time.time() - t}")



save_image_snappy: 3.7878315448760986
save_image: 12.264774322509766
save_image_fast: 15.478008508682251
save_image_pth: 3.5136613845825195

-rw-r--r-- 1 nagadomi nagadomi   78998  8月 22 00:38 miku_CC_BY-NC.jpg
-rw-r--r-- 1 nagadomi nagadomi  246365  9月  3 09:42 miku_fast.png
-rw-r--r-- 1 nagadomi nagadomi 1080341  9月  3 09:42 miku_fast.pth
-rw-r--r-- 1 nagadomi nagadomi  380019  9月  3 09:42 miku_fast.sz
"""
