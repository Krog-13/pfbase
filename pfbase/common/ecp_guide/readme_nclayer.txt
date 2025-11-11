Функция для подписания данных по ЭЦП.

Порядок исполнения:
1. Фронт подключается к веб-сокету NCLayer
2. NCLayer принимает сертификат, подготавливает зашифрованные данные для отправки в бэкенд
3. Формат тела выглядит примерно таким образом

-----BEGIN CMS-----
MIINQgYJKoZIhvcNAQcCoIINMzCCDS8CAQExDjAMBggqgw4DCgEDAwUAMAsGCSqG
SIb3DQEHAaCCBFswggRXMIIDv6ADAgECAhQfkTQ25nr/LmQduKhv9sMo7PIG2jAO
...
...
qNirF+zSkBeenxOTAFQNOG8BLRlTbOEdPHRas5pwpnDEqR++1NE=
-----END CMS-----

4. Бэкенд получает данные для верификации с помощью библиотеки pykalkan + SDK.

=========Настройка сервера для работы с ЭЦП============
На сервер скопировать
 - SDK папку production
 - install_production.sh скрипт установки



===============Пример реализации на бэкенде================
см. file verify_cms.py


===============Пример реализации на фронте================

Необходимо Js библиотека ncalayer-js-client==1.5.6, метод шифрования kz.gov.pki.knca.basics (базовое)
https://github.com/sigex-kz/ncalayer-js-client      библиотека NCALayerClient
https://sigex-kz.github.io/ncalayer-js-client/api/  документация API
Пример кода на Vue JavaSrcipt указан ниже

// ncalayer-client.js
нужный метод на строке 832 createCAdESFromBase64
см. file ecp.vue
