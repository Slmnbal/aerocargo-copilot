# Rota Önceliklendirme Kuralları

## Amaç
Kapasite kısıtlı olduğunda, hangi rotaların öncelikli olarak desteklenmesi gerektiğini tanımlar.

## Önceliklendirme Mantığı

Rotalar, tarihsel talep hacmine göre ağırlıklandırılır: yüksek talepli bir rotaya ayrılan bir birim kapasite, düşük talepli bir rotaya ayrılan bir birim kapasiteden daha değerli kabul edilir. Bu, kısıtlı kaynağın toplam fayda açısından en verimli şekilde dağıtılmasını sağlar.

## Dengeleyici Kurallar

Salt talep bazlı önceliklendirme tek başına yeterli değildir, çünkü şunlara yol açabilir:

- **Düşük talepli rotaların tamamen terk edilmesi** → Minimum Hizmet Seviyesi kuralıyla önlenir (bkz. Kapasite Planlama Politikası).
- **Kapasitenin birkaç rotada aşırı yoğunlaşması** → Yoğunlaşma Sınırı kuralıyla önlenir.

## Sonuç

Önceliklendirme, saf talep sıralaması değil; talep ağırlığı ile minimum hizmet ve risk dağıtımı kurallarının birlikte dengelendiği bir karardır.
