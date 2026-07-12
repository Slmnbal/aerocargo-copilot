# Aksama Yönetimi (Disruption Management)

## Amaç
Beklenmeyen aksamalar (hava koşulları, teknik arıza, personel yetersizliği) durumunda izlenecek karar mantığını tanımlar.

## Temel Yaklaşım

Bir aksama durumunda, öncelik sırası şu şekildedir:

1. **Yüksek talepli / yüksek yoğunluklu rotaların korunması**: Rota Önceliklendirme Kuralları'na göre ağırlığı yüksek olan rotalarda hizmet sürekliliği önceliklidir.
2. **Havalimanı slot kısıtlarının yeniden değerlendirilmesi**: Aksama süresince, etkilenen havalimanının slot kapasitesi geçici olarak düşürülmüş kabul edilir, kapasite/rota modeli bu yeni sınırla yeniden çalıştırılmalıdır.
3. **Minimum hizmet seviyesinin korunması**: Aksama durumunda dahi, düşük öncelikli rotalar tamamen iptal edilmeden önce diğer esneklikler (zamanlama, alternatif rota) değerlendirilir.

## Not

Aksama yönetimi, statik bir plan değil; kapasite/rota optimizasyon modelinin güncellenmiş kısıtlarla **yeniden çalıştırılmasını** gerektiren dinamik bir süreçtir.
