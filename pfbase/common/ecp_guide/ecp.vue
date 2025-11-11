import axios from 'axios';
import { NCALayerClient } from 'ncalayer-js-client';
import { NCALayerClient } from "@/ncalayer-client.js"

// Упращенный пример функции подписания данных
async function signDataWithNCALayer(dataToSign) {
    const nca = new NCALayerClient()
    await nca.connect()

    // Пример простых данных для подписи, это может list, map, pdf и т.д.
    const simpleData = {
        author: "admin",
        department: "kmg",
        doc_date: "2024-03-10",
        doc_number: "110550-12"
    };

    const jsonString = JSON.stringify(simpleData);
    const base64Data = btoa(new TextEncoder().encode(jsonString).reduce((acc, byte) => acc + String.fromCharCode(byte), ""));

    // const result = await nca.createCAdESFromBase64("PKCS12", base64Data, "SIGNATURE", true);
    const result = await nca.createCAdESFromBase64("PKCS12", base64Data);

    console.log("data", base64Data);
    console.log("signature", result);

    // Отправка на бэкенд
    const body_backend = {
        data: base64Data,
        signature: result
    }