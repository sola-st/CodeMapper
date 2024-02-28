# load codebert-base model
import os
import torch
from transformers import RobertaTokenizer, RobertaModel

local_model_dir = "data/pretrained_model"
os.makedirs(local_model_dir, exist_ok=True)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = RobertaTokenizer.from_pretrained("microsoft/codebert-base")
model = RobertaModel.from_pretrained("microsoft/codebert-base")
model.to(device)

tokenizer.save_pretrained(local_model_dir)
model.save_pretrained(local_model_dir)