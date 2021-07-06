import trankit

# initialize a trainer for the task
trainer = trankit.TPipeline(
    training_config={
    'max_epoch': 50,
    'category': 'customized-ner',  # pipeline category
    'task': 'ner', # task name
    'save_dir': './save_dir', # directory to save the trained model
    'train_bio_fpath': './train.bio', # training data in BIO format
    'dev_bio_fpath': './dev.bio' # training data in BIO format
    }
)

# start training
trainer.train()