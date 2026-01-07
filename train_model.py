import torch
import torch.nn as nn
import torch.optim as optim
import json
import random
from pathlib import Path
from torch.utils.data import Dataset, DataLoader

# Configuration
BATCH_SIZE = 32
EPOCHS = 5
EMBED_DIM = 64
HIDDEN_DIM = 128
MAX_SEQ_LEN = 10
NUM_SAMPLES = 500

# Special Tokens
PAD_IDX = 0
SOS_IDX = 1
EOS_IDX = 2
SPECIAL_TOKENS_COUNT = 3

# Load Tokenizer
tokenizer_path = Path(__file__).parent / "dsl_tokenizer.json"
with open(tokenizer_path, encoding="utf-8") as f:
    tokenizer_data = json.load(f)

token_to_id = tokenizer_data["token_to_id"]
id_to_token = tokenizer_data["id_to_token"]

# Calculate Vocab Size
# Max ID in tokenizer + 1 (for 0-based indexing) + Special Tokens offset
max_id = max(int(v) for v in token_to_id.values())
VOCAB_SIZE = max_id + 1 + SPECIAL_TOKENS_COUNT
print(f"Vocab Size: {VOCAB_SIZE}")


# Model Definition (Must match inference_dsl.py)
class LSTMEncoderDecoder(nn.Module):
    def __init__(self, vocab_size, embed_dim=64, hidden_dim=128):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embed_dim, padding_idx=PAD_IDX)
        self.encoder = nn.LSTM(embed_dim, hidden_dim, batch_first=True)
        self.decoder = nn.LSTM(embed_dim, hidden_dim, batch_first=True)
        self.fc_out = nn.Linear(hidden_dim, vocab_size)

    def forward(self, x, target=None, teacher_forcing_ratio=0.5):
        # x: (batch, seq_len)
        batch_size = x.size(0)
        target_len = x.size(1) if target is None else target.size(1)

        emb = self.embed(x)
        _, (h, c) = self.encoder(emb)

        dec_input = torch.full(
            (batch_size, 1), SOS_IDX, dtype=torch.long, device=x.device
        )
        outputs = []

        for t in range(target_len):
            dec_emb = self.embed(dec_input)
            out, (h, c) = self.decoder(dec_emb, (h, c))
            logits = self.fc_out(out)  # (batch, 1, vocab)
            outputs.append(logits)

            if target is not None and random.random() < teacher_forcing_ratio:
                dec_input = target[:, t].unsqueeze(1)
            else:
                dec_input = logits.argmax(dim=-1)

        return torch.cat(outputs, dim=1)


# Dataset
class DSLDataset(Dataset):
    def __init__(self, num_samples, max_len, token_ids):
        self.data = []
        for _ in range(num_samples):
            seq_len = random.randint(3, max_len)
            seq = random.choices(token_ids, k=seq_len)
            self.data.append(seq)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        # Input: [ID, ID, ...] -> Shifted by 3
        raw_seq = self.data[idx]
        input_seq = [x + SPECIAL_TOKENS_COUNT for x in raw_seq]
        return torch.tensor(input_seq, dtype=torch.long)


def collate_fn(batch):
    # Pad sequences
    max_len = max(len(s) for s in batch)
    padded_batch = torch.full((len(batch), max_len), PAD_IDX, dtype=torch.long)
    for i, seq in enumerate(batch):
        padded_batch[i, : len(seq)] = seq
    return padded_batch


# Training
def train():
    all_token_ids = list(token_to_id.values())
    dataset = DSLDataset(NUM_SAMPLES, MAX_SEQ_LEN, all_token_ids)
    dataloader = DataLoader(
        dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_fn
    )

    model = LSTMEncoderDecoder(VOCAB_SIZE, EMBED_DIM, HIDDEN_DIM)
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss(ignore_index=PAD_IDX)

    model.train()
    print("Training started...")
    for epoch in range(EPOCHS):
        total_loss = 0
        for batch in dataloader:
            optimizer.zero_grad()

            # Target is same as input (Autoencoder)
            output = model(batch, target=batch)  # (batch, seq_len, vocab)

            # Flatten for loss
            output_flat = output.view(-1, VOCAB_SIZE)
            target_flat = batch.view(-1)

            loss = criterion(output_flat, target_flat)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{EPOCHS}, Loss: {total_loss/len(dataloader):.4f}")

    # Save Model
    save_path = Path(__file__).parent / "model.pt"
    torch.save(model.state_dict(), save_path)
    print(f"Model saved to {save_path}")


if __name__ == "__main__":
    train()
