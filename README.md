# Bn_hanwritten_text_detection
The DBnet model was trained by my custom Bangli handwritten or Font image dataset to Bangli text word.

# Dependency
- python == 3.6
- torch == 1.4.0
- torchvision == 0.5.0
- colorlog 
- polygon3 
- opencv-python
# Data structure

Convert the vgg annotation into 8 coordinate.

so the txt file annotation like this,
```
x,y,w,h convert below coordinate

w,h = x+weight,y+height
x1,y1,x2,y2,x3,y3,x4,y4 = x,y,w,y,w,h,x,h
```

```
datasets
├── test.txt
├── train
│   ├── gt
│   │   └── 11b2e8556cc7f36da563dfafc447f4da.txt
│   └── img
│       └── 11b2e8556cc7f36da563dfafc447f4da.jpg
├── train.txt
└── val
    ├── gt
    │   └── 3648c8fb0771c3dd91fd3321b70bc0ca.txt
    └── img
        └── 3648c8fb0771c3dd91fd3321b70bc0ca.jpg
```
