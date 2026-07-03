from torch.utils.tensorboard import SummaryWriter

writer = SummaryWriter("runs/stage4_test")

for step in range(20):
    loss = 1.0 / (step + 1)
    accuracy = step / 20
    writer.add_scalar("Loss/train", loss, step)
    writer.add_scalar("Accuracy/train", accuracy, step)

writer.close()
print("TensorBoard log written to runs/stage4_test")
