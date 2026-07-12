# Kapasite Planlama Politikası

## Amaç
Bu doküman, AeroCargo operasyonlarında kapasite ve rota atama kararlarında izlenen temel ilkeleri tanımlar.

## Temel İlkeler

1. **Toplam Filo Kapasitesi**: Herhangi bir planlama döneminde toplam operasyon, mevcut filo kapasitesinin tarihsel talebin en fazla %60'ı ile sınırlıdır. Bu, bakım, yedek kapasite ve beklenmeyen aksamalar için tampon bırakır.

2. **Havalimanı Slot Kısıtı**: Her havalimanının kalkış kapasitesi, o havalimanının tarihsel toplam talebinin %50'si ile sınırlıdır. Bu kısıt, havalimanı altyapı kapasitesini ve slot tahsis kurallarını yansıtır.

3. **Minimum Hizmet Seviyesi**: Aktif bir rota, tarihsel talebinin en az %10'u kadar kapasiteyle desteklenmelidir. Bu ilke, pazar kaybının ve marka güveninin korunması içindir.

4. **Yoğunlaşma Sınırı**: Tek bir rota, toplam filo kapasitesinin %25'inden fazlasını kullanamaz. Bu, operasyonel riskin (örn. tek bir rotada yaşanacak aksamanın tüm operasyonu etkilememesi) dağıtılması içindir.

## Uygulama
Bu ilkeler, kapasite/rota optimizasyon modelinin kısıtlarını oluşturur.
