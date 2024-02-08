// readlineとnode-fetchをインポートします
import * as readline from 'readline';
import fetch from 'node-fetch';
// Web APIのURLを定義します
const url = "https://webapi-8trs.onrender.com/ask";
// readlineのインターフェースを作成します。inputとoutputはユーザーの入力と出力(コンソール)を指定します
const ask = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});
// AI関数を定義します
const AI = () => {
    // ユーザーに質問を投げかけ、その回答を非同期で処理します
    ask.question("💬コメント:", async (api) => {
        // ユーザーの回答をURLエンコードします
        const ask = encodeURIComponent(api);
        try {
            // Web APIにリクエストを送り、そのレスポンスを待ちます
            const response = await fetch(`${url}?text=${ask}`);
            // レスポンスをJSON形式で解析します
            const body = await response.json();
            // 解析した結果をコンソールに出力します
            console.log(body);
            // 再度AI関数を呼び出します
            AI();
        }
        catch (err) {
            // エラーが発生した場合はそれをコンソールに出力します
            console.error(`ERROR${err}`);
        }
    });
};
// AI関数を初めて呼び出します
AI();
