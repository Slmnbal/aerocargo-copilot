from datasets import load_dataset

# Hugging Face'teki veri setini indir
dataset = load_dataset("Kabil007/IndianDomesticAirlineDataset")

# Hangi split'ler var, önce onu görelim
print(dataset)

# İlk split'i pandas DataFrame'e çevir
df = dataset[list(dataset.keys())[0]].to_pandas()

# Sütunlar ve veri tipleri
print(df.info())

# İlk 5 satır
print(df.head())