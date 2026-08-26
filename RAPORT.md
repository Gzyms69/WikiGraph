# 📊 Raport z Audytu Technicznego: WikiGraph (Wersja Poprawiona)

**Data:** 13 Marca 2026
**Podejście:** Bezlitosna krytyka techniczna, analiza długu technologicznego, ścieżka AI oraz strategia darmowego hostingu.

---

## 1. Bezlitosny Audyt Pipeline'u i Kodu

Projekt z zewnątrz wygląda imponująco (grafika 3D, miliardy krawędzi), ale pod spodem kryje poważny dług techniczny, który dyskwalifikuje go w oczach rekrutera na stanowisko Mid/Regular AI Engineer, dopóki nie zostanie naprawiony.

### Krok 1: Inicjalizacja i Setup (`setup_environment.sh`)
*   **Krytyka:** Skrypt zakłada idealny świat. Nie weryfikuje, czy użytkownik ma odpowiednią wersję Pythona (wymagane 3.10+) ani Node.js (wymagane 18+). Co gorsza, skrypt kopiuje `.env.example`, którego... **nie ma w repozytorium**. Aplikacja wstanie, ale po cichu wywali się przy próbie odpytania API Gemini.
*   **Jakość kodu:** 5/10 | **Funkcjonalność:** 5/10 | **Portfolio:** 4/10 | **Gotowość AI:** 3/10

### Krok 2: Ekstrakcja i Pipeline (`core/pipeline/`)
*   **Krytyka:** Proces jest mocny operacyjnie (np. fallback na `aria2c`, użycie WAL w SQLite, multiprocessing przy parsowaniu), ale skrypt `extract_infoboxes.py` łamie się na zjawisku *Schema Drift* (np. niemiecka Wikipedia używa tabel HTML zamiast szablonów infoboksów). Moduł przygotowujący CSV dla Neo4j ładuje mapowanie ID do pamięci RAM jako słownik, co przy dużej Wikipedii wysadzi lokalną maszynę z 16GB RAM.
*   **Jakość kodu:** 7/10 | **Funkcjonalność:** 6/10 | **Portfolio:** 7/10 | **Gotowość AI:** 6/10

### Krok 3: API Backend (`app/main.py` i routery)
*   **Krytyka:** Architektura *Virtual Bridge* jest świetna, ale wykonanie ma ogromne luki bezpieczeństwa i jakości. W pliku `neo4j_manager.py` znajduje się 75 linii "myślenia na głos" w komentarzach na temat implementacji timeoutów – to absolutnie niedopuszczalne na produkcji. Konfiguracja CORS (`allow_origins=["*"]`) wpuszcza każdy ruch, a hasła do Neo4j są wkompilowane w kod (`auth=("neo4j", "wikigraph")`). Brak jakiegokolwiek Rate Limitingu sprawia, że wystawienie tego na zewnątrz skończy się wyczerpaniem budżetu Gemini API w godzinę.
*   **Jakość kodu:** 5/10 | **Funkcjonalność:** 8/10 | **Portfolio:** 6/10 | **Gotowość AI:** 7/10

### Krok 4: Frontend (`frontend/`)
*   **Krytyka:** Użycie TypeScriptu w tym projekcie to fikcja. W kluczowym pliku `WikiNebula.tsx` występuje typ `any`, co niszczy całe bezpieczeństwo języka. Połączenie z API jest zahardkodowane (`http://localhost:8000`), a aplikacja nie posiada *Error Boundary* – jeśli graf 3D "chrupnie", użytkownik zobaczy tylko biały ekran.
*   **Jakość kodu:** 5/10 | **Funkcjonalność:** 7/10 | **Portfolio:** 7/10 | **Gotowość AI:** 6/10

### Krok 5: Infrastruktura Testowa (NAJWIĘKSZY PROBLEM)
*   **Krytyka:** Folder `tests/` to śmietnik skryptów walidacyjnych odpalanych z palca. Brak frameworka `pytest`, brak testów jednostkowych, brak pipeline'u CI/CD w GitHub Actions. Z punktu widzenia komercyjnej inżynierii oprogramowania ten kod jest nietestowalny.
*   **Jakość kodu:** 2/10 | **Funkcjonalność:** 3/10 | **Portfolio:** 2/10 | **Gotowość AI:** 2/10

---

## 2. Plan Naprawczy (Pre-AI Hardening)

Zanim dodasz jakiekolwiek nowe funkcje ML, musisz posprzątać ten bałagan (wg planu z `TODO.md`):
1.  **Testy:** Wdrożyć `pytest`, napisać podstawowe testy dla API oraz wpiąć to w GitHub Actions (aby testy odpalały się przy każdym pushu).
2.  **Środowisko:** Stworzyć brakujący `.env.example`, wyrzucić hasła z kodu do zmiennych środowiskowych.
3.  **Frontend:** Pozbyć się typów `any` i dodać `NEXT_PUBLIC_API_URL`.
4.  **Backend:** Usunąć 75 linii bełkotu z `neo4j_manager.py` i naprawić CORS.

---

## 3. Strategia wdrażania AI (Przewaga na rynku)

Twój plan rozbudowy z `TODO.md` to strzał w dziesiątkę. Obecny endpoint to zwykły *prompt-stuffing*. Żeby dostać pracę jako Inżynier AI, musisz wdrożyć **GraphRAG**.

### Etap 1: Semantic Search
Obecnie szukasz tylko po słowach kluczowych (FTS5). Musisz dodać wektoryzację.
*   **Zadanie:** Skrypt wciągający teksty z Wikipedii, przepuszczający je przez model `sentence-transformers` na lokalnym CPU i zapisujący wektory do bazy. Najlepszym, bezserwerowym rozwiązaniem będzie zainstalowanie rozszerzenia `sqlite-vec` bezpośrednio do Twojego istniejącego SQLite.

### Etap 2: GraphRAG (Text-to-Cypher + Kontekst)
Zamiast szukać w tekście, każesz modelowi językowemu napisać zapytanie do bazy grafowej.
*   **Zadanie:** Tworzysz agenta, który tłumaczy język naturalny ("Jakie miasta w Polsce są najbliżej powiązane z IT?") na język zapytań Cypher dla Neo4j. Następnie Agent pobiera te konkretne węzły, czyta ich tekst z bazy wektorowej i generuje idealną, pozbawioną halucynacji odpowiedź. To gwarantuje stanowisko Mida na obecnym rynku.

---

## 4. Architektura "Portfolio Demo" (Darmowy Hosting)

Doszliśmy do najważniejszego punktu. Neo4j z Graph Data Science pochłania **minimum 8 GB RAM**. Darmowe hostingi (Vercel, Render, Fly.io) dają od 256 MB do 512 MB RAM. W obecnej architekturze **nie wystawisz tego za darmo do internetu**. Pokażę Ci, jak obejść ten problem z punktu widzenia Architekta.

Aby wystawić to jako genialne demko, musisz zmienić architekturę z **Live Graph** na **Pre-computed Graph** (tzw. architekturę statycznego dema). 

### Plan Darmowego Hostingu (Krok po kroku):

1.  **Lokalne "Kopanie" Danych (Heavy Lifting):**
    Używasz swojego lokalnego komputera. Odpalasz pełen stos (Neo4j, SQLite). Budujesz bazę wektorową. Włączasz algorytmy GDS (PageRank, Jaccard, Louvain).
2.  **Baking (Eksport topologii do relacji):**
    Piszesz skrypt `tools/export_demo_graph.py`. Skrypt ten odpytuje Neo4j o np. 50 000 najważniejszych artykułów (najwyższy PageRank). Dla każdego artykułu wyciąga jego "top 20 sąsiadów" z uwzględnieniem siły połączeń. 
    Wszystkie te powiązania zapisujesz na stałe do bazy **SQLite** do nowej tabeli `precomputed_edges (source_qid, target_qid, weight)`.
3.  **Śmierć Neo4j:**
    W architekturze Demo **całkowicie usuwasz Neo4j z procesu**.
4.  **Refaktoryzacja Backend'u dla Dema:**
    Modyfikujesz kod FastAPI (tworząc wersję lub branch `portfolio-demo`), aby zamiast uderzać do `Neo4jManager`, czytał powiązania bezpośrednio ze statycznej tabeli SQLite. Algorytm ścieżek (BFS) zostaje napisany w czystym Pythonie operującym na krawędziach pobranych ze SQLite.
5.  **Deployment (Koszt: 0$):**
    *   **Baza Danych i Backend:** Plik `.db` zajmujący np. 500 MB (z metrykami, wektorami `sqlite-vec` i wyeksportowanymi krawędziami) ładujesz razem z kodem Pythona na darmowy tier na **Render.com** lub **Fly.io** (wystarczy najsłabszy kontener 512MB RAM, ponieważ SQLite zużywa pamięć mikroskopijnie).
    *   **Frontend:** Interfejs z Next.js kompilujesz statycznie i wrzucasz na **Vercel** (całkowicie darmowy).

### Podsumowanie dla Ciebie (Dlaczego to zadziała na rekruterów):
Pytanie na rekrutacji: *"Widzę, że masz graf. Dlaczego nie użyłeś Neo4j na produkcji?"*
Twoja odpowiedź: *"Zaprojektowałem pipeline oparty na Neo4j do analityki i treningu (co widać na moim GitHubie). Jednakże, aby zoptymalizować koszty utrzymania serwerów aplikacji B2C o 99%, wdrożyłem architekturę pre-computingu, która serializuje topologię do bazy SQLite i wektorów. Zmniejszyło to wymagania RAM serwera z 8GB do 250MB bez utraty funkcjonalności frontendu."*
**Wynik:** Rekruter zbiera szczękę z podłogi, ponieważ pokazujesz myślenie o biznesie i optymalizacji kosztów (tzw. FinOps), a nie tylko ślepe instalowanie modnych narzędzi.

---

## 5. Werdykt
Projekt jest fantastyczny pod kątem koncepcyjnym. Jeśli naprawisz w pierwszej kolejności błędy jakościowe wymienione w punkcie 1, a następnie dodasz bazę wektorową oraz wyeksportujesz graf do "wersji demo" opartej wyłącznie na lekkim SQLite, **bez problemu zdobędziesz pierwszą pracę w branży Data/AI Engineering.** Zbudowanie prawdziwego systemu GraphRAG to dowód wiedzy rzadko spotykany u początkujących.
