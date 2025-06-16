Функция для парсинга данных по ЭЦП.

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

4. Бэкенд получает текст сообщения и набор библиотек cryptography и asn1crypto распасивают на мелкие детали.
5. Функция parse_cms первым агрументом принимает набор текста шифрования, вторым аргументом personal или organization в зависимости от потребности
6. personal выдает следующие поля: 'commonName', 'surname', 'givenName', 'serialNumber',  'countryName'
7. organization выдает следующие поля: 'commonName', 'organizationName', 'organizationalUnitName', 'serialNumber', 'countryName'

8. Извлекать данные нетрудно: Достаточно написать parse_cms(signature_pem, 'organization')['payload'].get('serialNumber')
9. Чтобы узнать статус распарсен ли сертификат или нет parse_cms(signature_pem, 'organization')['success'], возвращает True или False




===============Пример реализации на фронте================

Необходимо Js библиотека ncalayer-js-client==1.5.5, метод шифрования kz.gov.pki.knca.basics (базовое)
Пример кода на ReactJs Typesrcipt указан ниже

// src/App.tsx
import React, { useState } from 'react';
import { NCALayerClient } from 'ncalayer-js-client';

interface SignedPayload {
  content: string;   // Base64 исходных данных
  signature: string; // PEM-обёртка CMS
}

async function connectAndSign(
  documentInBase64: string
): Promise<SignedPayload> {
  const client = new NCALayerClient();

  try {
    await client.connect();
  } catch (error) {
    throw new Error(`Не удалось подключиться к NCALayer: ${error}`);
  }

  let signature: string;
  try {
    signature = await client.basicsSignCMS(
      NCALayerClient.basicsStorageAll,
      documentInBase64,
      NCALayerClient.basicsCMSParamsDetached,
      NCALayerClient.basicsSignerSignAny
    );
  } catch (error: any) {
    if (error.canceledByUser) {
      throw new Error('Действие отменено пользователем.');
    }
    throw new Error(error.toString());
  }

  return { content: documentInBase64, signature };
}

export const App: React.FC = () => {
  const [iin, setIin] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    setError(null);
    setIin(null);
    setLoading(true);

    // Ваши данные, которые нужно подписать
    const documentInBase64 = btoa(unescape(encodeURIComponent(JSON.stringify({
      foo: 'bar',
      ts: Date.now()
    }))));

    try {
      // 1) Подписываем
      const payload = await connectAndSign(documentInBase64);

      const res = await fetch('http://127.0.0.1:8000/api/cms/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || res.statusText);
      }

      // 3) Читаем ответ (ожидаем { detail, iin })
      const data = await res.json() as { detail: string; iin: string };
      setIin(data.iin);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 24 }}>
      <h1>ЭЦП-подпись через NCALayer</h1>
      <button onClick={handleClick} disabled={loading}>
        {loading ? 'Подождите…' : 'Подписать и отправить'}
      </button>

      {iin && (
        <p style={{ marginTop: 16 }}>
          ✅ Подпись верна, ИИН: <b>{iin}</b>
        </p>
      )}

      {error && (
        <p style={{ marginTop: 16, color: 'red' }}>
          Ошибка: {error}
        </p>
      )}
    </div>
  );
};

export default App;
