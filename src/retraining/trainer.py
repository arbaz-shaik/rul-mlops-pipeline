import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import torch
from torch.utils.data import DataLoader, TensorDataset

from src.model.lstm import RULModel


x_train = np.load("./data/processed/x_train.npy")
y_train = np.load("./data/processed/y_train.npy")
y_train = np.minimum(y_train, 125)

x_train, x_val, y_train, y_val = train_test_split(
    x_train,
    y_train,
    test_size=0.2,
    random_state=42
)


y_train = y_train.reshape(-1, 1)
y_val = y_val.reshape(-1, 1)

train_dataset = TensorDataset(
    torch.tensor(x_train, dtype=torch.float32),
    torch.tensor(y_train, dtype=torch.float32)
)

val_dataset = TensorDataset(
    torch.tensor(x_val, dtype=torch.float32),
    torch.tensor(y_val, dtype=torch.float32)
)

train_dataloader = DataLoader(
    train_dataset,
    batch_size=32,
    shuffle=True
)

val_dataloader = DataLoader(
    val_dataset,
    batch_size=32,
    shuffle=False
)

print(f"y_train min: {y_train.min()}")
print(f"y_train max: {y_train.max()}")
print(f"y_train mean: {y_train.mean()}")

pred_model = RULModel(
    input_size=x_train.shape[2],
    hidden_size_1=64,
    hidden_size_2=32,
    dropout=0.2
)

optimizer = torch.optim.Adam(pred_model.parameters(), lr=0.001)
loss_fn = torch.nn.MSELoss()

best_rmse = float("inf")
patience_counter = 0
num_epochs = 50

for epoch in range(num_epochs):

    pred_model.train()

    running_loss = 0.0

    for batch_x, batch_y in train_dataloader:

        optimizer.zero_grad()

        outputs = pred_model(batch_x)

        loss = loss_fn(outputs, batch_y)

        loss.backward()

        optimizer.step()

        running_loss += loss.item()

    train_loss = running_loss / len(train_dataloader)

    pred_model.eval()

    predictions = []
    targets = []

    with torch.no_grad():

        for batch_x, batch_y in val_dataloader:

            outputs = pred_model(batch_x)

            predictions.extend(outputs.cpu().numpy())

            targets.extend(batch_y.cpu().numpy())

    val_rmse = np.sqrt(mean_squared_error(targets, predictions))

    if val_rmse < best_rmse:

        best_rmse = val_rmse
        patience_counter = 0

        torch.save(pred_model.state_dict(), "best_model.pth")

    else:

        patience_counter += 1

    print(
        f"Epoch [{epoch + 1}/{num_epochs}] "
        f"Train Loss: {train_loss:.4f} "
        f"Validation RMSE: {val_rmse:.4f}"
    )

    if patience_counter >= 10:
        print("Early stopping triggered.")
        break

print(f"Best Validation RMSE: {best_rmse:.4f}")