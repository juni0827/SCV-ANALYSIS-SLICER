
import torch
import torch.nn as nn
import json

# Load tokenizer
with open("dsl_tokenizer.json", encoding="utf-8") as f:
    tokenizer = json.load(f)

token_to_id = {k: int(v) for k, v in tokenizer["token_to_id"].items()}
id_to_token = {int(k): v for k, v in tokenizer["id_to_token"].items()}

PAD_IDX = 0
SOS_IDX = 1
EOS_IDX = 2
VOCAB_SIZE = len(token_to_id) + 3

class LSTMEncoderDecoder(nn.Module):
    def __init__(self, vocab_size, embed_dim=64, hidden_dim=128):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embed_dim, padding_idx=PAD_IDX)
        self.encoder = nn.LSTM(embed_dim, hidden_dim, batch_first=True)
        self.decoder = nn.LSTM(embed_dim, hidden_dim, batch_first=True)
        self.fc_out = nn.Linear(hidden_dim, vocab_size)

    def forward(self, x):
        emb = self.embed(x)
        _, (h, c) = self.encoder(emb)
        dec_input = torch.full((x.size(0), 1), SOS_IDX, dtype=torch.long, device=x.device)
        outputs = []

        for _ in range(x.size(1)):
            dec_emb = self.embed(dec_input)
            out, (h, c) = self.decoder(dec_emb, (h, c))
            logits = self.fc_out(out)
            outputs.append(logits)
            dec_input = logits.argmax(dim=-1)

        return torch.cat(outputs, dim=1)

    def generate(self, x, max_len=10):
        self.eval()
        with torch.no_grad():
            emb = self.embed(x)
            _, (h, c) = self.encoder(emb)
            dec_input = torch.full((x.size(0), 1), SOS_IDX, dtype=torch.long, device=x.device)
            outputs = []

            for _ in range(max_len):
                dec_emb = self.embed(dec_input)
                out, (h, c) = self.decoder(dec_emb, (h, c))
                logits = self.fc_out(out)
                pred = logits.argmax(dim=-1)
                outputs.append(pred)
                dec_input = pred
                if (pred == EOS_IDX).all():
                    break

        return torch.cat(outputs, dim=1)


model = LSTMEncoderDecoder(VOCAB_SIZE)
model.load_state_dict(torch.load("model.pt", map_location="cpu"))
model.eval()


def predict_dsl(input_tokens):
    # input_tokens: list of strings (e.g., ["C2", "C1", "C6"])
    input_ids = [token_to_id[token] + 3 for token in input_tokens]
    input_tensor = torch.tensor([input_ids])
    output_ids = model.generate(input_tensor)[0]
    return [id_to_token[i.item() - 3] for i in output_ids if i.item() >= 3]
