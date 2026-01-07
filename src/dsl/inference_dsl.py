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

# 모델 호환성을 위한 토큰 필터링
# 모델이 15개 토큰으로 학습된 것으로 보임 (VOCAB_SIZE=15)
SUPPORTED_TOKENS = [
    "C1",
    "C2",
    "C3",
    "C4",
    "C5",
    "C6",
    "C7",
    "C8",
    "C9",
    "C10",
    "C11",
    "C12",
]
VOCAB_SIZE = 15  # 모델이 학습된 어휘 크기


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
        dec_input = torch.full(
            (x.size(0), 1), SOS_IDX, dtype=torch.long, device=x.device
        )
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
            dec_input = torch.full(
                (x.size(0), 1), SOS_IDX, dtype=torch.long, device=x.device
            )
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
    # 지원되지 않는 토큰 필터링
    supported_tokens = [token for token in input_tokens if token in SUPPORTED_TOKENS]

    if not supported_tokens:
        print("  지원되는 토큰이 없습니다. 기본 시퀀스를 사용합니다.")
        return input_tokens

    # 모델이 사용 가능한 경우만 예측 시도
    if not MODEL_AVAILABLE:
        return input_tokens

    try:
        # 지원되는 토큰만 사용해서 예측
        token_mapping = {token: idx for idx, token in enumerate(SUPPORTED_TOKENS)}
        input_ids = [token_mapping.get(token, 0) + 3 for token in supported_tokens]
        input_tensor = torch.tensor([input_ids])
        output_ids = model.generate(input_tensor)[0]

        # 예측 결과를 토큰으로 변환
        predicted_tokens = []
        for i in output_ids:
            idx = i.item() - 3
            if 0 <= idx < len(SUPPORTED_TOKENS):
                predicted_tokens.append(SUPPORTED_TOKENS[idx])

        return predicted_tokens if predicted_tokens else input_tokens

    except Exception as e:
        print(f"  예측 중 오류 발생: {e}")
        return input_tokens
