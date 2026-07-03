import time
import torch

print("PyTorch:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
print("CUDA runtime used by PyTorch:", torch.version.cuda)
print("cuDNN version:", torch.backends.cudnn.version())
print("GPU count:", torch.cuda.device_count())

if not torch.cuda.is_available():
    raise SystemExit("CUDA is not available to PyTorch")

device = torch.device("cuda")
gpu_name = torch.cuda.get_device_name(0)
props = torch.cuda.get_device_properties(0)

print("GPU:", gpu_name)
print("Total VRAM GB:", round(props.total_memory / 1024**3, 2))
print("Compute capability:", f"{props.major}.{props.minor}")

x = torch.randn((4096, 4096), device=device)
y = torch.randn((4096, 4096), device=device)

torch.cuda.synchronize()
start = time.time()

z = x @ y

torch.cuda.synchronize()
elapsed = time.time() - start

print("Matrix multiply shape:", tuple(z.shape))
print("Elapsed seconds:", round(elapsed, 4))
print("CUDA PyTorch test OK")
