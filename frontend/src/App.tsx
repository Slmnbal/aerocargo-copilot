import { useState } from "react";
import { Chat } from "./components/Chat";
import { Forecast } from "./components/Forecast";

type Sekme = "sohbet" | "tahmin";

function App() {
  const [sekme, setSekme] = useState<Sekme>("sohbet");

  return (
    <div className="mx-auto flex h-screen max-w-2xl flex-col bg-white text-neutral-900 dark:bg-neutral-950 dark:text-neutral-100">
      <header className="border-b border-neutral-200 px-4 py-3 dark:border-neutral-800">
        <h1 className="text-lg font-semibold">AeroCargo Copilot</h1>
        <p className="text-xs text-neutral-500 dark:text-neutral-400">
          Kapasite/rota optimizasyonu, operasyonel politikalar ve talep tahmini
        </p>
        <nav className="mt-3 flex gap-1">
          {(["sohbet", "tahmin"] as const).map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setSekme(s)}
              className={`rounded-md px-3 py-1.5 text-sm font-medium ${
                sekme === s
                  ? "bg-indigo-600 text-white"
                  : "text-neutral-600 hover:bg-neutral-100 dark:text-neutral-300 dark:hover:bg-neutral-900"
              }`}
            >
              {s === "sohbet" ? "Sohbet" : "Talep Tahmini"}
            </button>
          ))}
        </nav>
      </header>
      <main className="flex-1 overflow-hidden">
        {sekme === "sohbet" ? <Chat /> : <Forecast />}
      </main>
    </div>
  );
}

export default App;
