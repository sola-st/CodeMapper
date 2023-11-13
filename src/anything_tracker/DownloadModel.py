from sentence_transformers import SentenceTransformer


def load_model(model_name, model_path):
    model = SentenceTransformer(model_name)
    model.save(model_path)

if __name__=="__main__":
    pretrained_model_name = "all-MiniLM-L6-v2"
    model_path = "data/pretrained_model"
    load_model(pretrained_model_name, model_path)