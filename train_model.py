from rasa_nlu.training_data import load_data
from rasa_nlu.config import RasaNLUModelConfig
from rasa_nlu.model import Trainer
from rasa_nlu import config

training_data = load_data('data/demo-rasa_zh.json')
trainer = Trainer(config.load("config_jieba_mitie_sklearn.yml"))
trainer.train(training_data)
model_directory = trainer.persist('./models/')