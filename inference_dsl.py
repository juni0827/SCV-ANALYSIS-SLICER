
import torch
import torch.nn as nn
import json
from pathlib import Path

# Load tokenizer - support both old and new paths
tokenizer_path = Path(__file__).parent / "dsl_tokenizer.json"
if not tokenizer_path.exists():
    tokenizer_path = Path("dsl_tokenizer.json")
with open(tokenizer_path, encoding="utf-8") as f:
    tokenizer = json.load(f)

token_to_id = {k: int(v) for k, v in tokenizer["token_to_id"].items()}
id_to_token = {int(k): v for k, v in tokenizer["id_to_token"].items()}

PAD_IDX = 0
SOS_IDX = 1
EOS_IDX = 2
SPECIAL_TOKENS_COUNT = 3

# Calculate VOCAB_SIZE dynamically
max_id = max(token_to_id.values()) if token_to_id else 0
VOCAB_SIZE = max_id + 1 + SPECIAL_TOKENS_COUNT

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

# 모델 로드 - support both old and new paths
try:
    model = LSTMEncoderDecoder(VOCAB_SIZE)
    model_path = Path(__file__).parent / "model.pt"
    if not model_path.exists():
        model_path = Path("model.pt")
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()
    MODEL_AVAILABLE = True
except Exception as e:
    print(f"  ML 모델 로드 실패: {e}")
    print("기본 시퀀스를 사용합니다.")
    MODEL_AVAILABLE = False

def predict_dsl(input_tokens):
    """DSL 토큰 예측"""
    if not input_tokens:
        return input_tokens
    
    if not MODEL_AVAILABLE:
        return input_tokens
    
    try:
        # Convert tokens to IDs
        input_ids = []
        for token in input_tokens:
            if token in token_to_id:
                # Shift by SPECIAL_TOKENS_COUNT
                input_ids.append(token_to_id[token] + SPECIAL_TOKENS_COUNT)
        
        if not input_ids:
            return input_tokens

        input_tensor = torch.tensor([input_ids])
        output_ids = model.generate(input_tensor)[0]
        
        # Convert IDs back to tokens
        predicted_tokens = []
        for i in output_ids:
            idx = i.item() - SPECIAL_TOKENS_COUNT
            if idx in id_to_token:
                predicted_tokens.append(id_to_token[idx])
        
        return predicted_tokens if predicted_tokens else input_tokens
        
    except Exception as e:
        print(f"  예측 중 오류 발생: {e}")
        return input_tokens
