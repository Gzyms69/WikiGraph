# WikiGraph -- Raport z Audytu Technicznego

**Data:** 2026-03-13
**Audytor:** Antigravity AI Agent
**Wersja projektu:** Aktualny stan repozytorium (commit HEAD)
**Zakres:** Pelen pipeline uzytkowania + jakosc kodu + gotowosc AI + wartosc portfolio

---

## Skala Ocen (1-10)

| Ocena | Znaczenie |
|:---:|:---|
| 1-3 | Krytyczne braki, wymaga przepisania |
| 4-5 | Dzialajace, ale ze znaczacymi problemami |
| 6-7 | Solidne, wymaga ulepszen |
| 8-9 | Profesjonalne, drobne poprawki |
| 10 | Produkcyjne, wzorowe |

---

# CZESC 1: AUDYT PIPELINE'U

Pipeline od `git clone` do interakcji w przegladarce sklada sie z 8 odredznych etapow. Ponizej krytyczna analiza kazdego z nich.

---

## Etap 1: Klonowanie i Setup Srodowiska

**Pliki:** [setup_environment.sh](file:///home/gzyms/Dev%20Projects/WikiGraph/setup_environment.sh), [README.md](file:///home/gzyms/Dev%20Projects/WikiGraph/README.md)

### Co robi
Skrypt `setup_environment.sh` wykonuje 4 kroki: tworzy venv Pythona, instaluje `requirements.txt`, uruchamia `npm install` dla frontendu, kopiuje `.env.example` do `.env`, i sprawdza obecnosc Dockera.

### Ocena krytyczna

**Mocne strony:**
- Skrypt jest idempotentny (sprawdza czy venv juz istnieje)
- Uzywanie `npm ci` gdy `package-lock.json` istnieje -- to poprawna praktyka
- Wykrywanie braku Pythona i npm z czytelnymi komunikatami
- Pipeline posiada `set -e` (fail-fast)

**Slabe strony:**
- Brak weryfikacji wersji Pythona (moze ruszyc na Python 3.8, co nie jest gwarantowane przez zaleznosci)
- Brak weryfikacji wersji Node.js (Next.js 14+ wymaga Node 18+)
- `.env.example` -- sprawdzilem, plik nie istnieje w repozytorium. Skrypt wyrzuci blad "not found" i przejdzie dalej bez `.env`, co spowoduje pozniej ciche awarie FastAPI (brak `GEMINI_API_KEY`)
- Brak automatycznego tworzenia directory structure dla `data/raw/`, `logs/`, `data/neo4j_data/`
- README.md opisuje pipeline, ale nie podaje minimalnych wymagan sprzetowych (RAM, dysk). To krytyczne, bo polskie dumpy Wikipedii to ~10GB, a Neo4j z GDS potrzebuje minimum 8GB RAM

### Sugestie poprawek
1. Dodac walidacje wersji: `python3 --version | grep -E "3\.(10|11|12|13)"` 
2. Stworzyc `.env.example` z komentarzami do kazdej zmiennej
3. Dodac sekcje "System Requirements" do README
4. Dodac automatyczne tworzenie katalogow `data/raw/{lang}` i `logs/`

| Metryka | Ocena | Argumentacja |
|:---|:---:|:---|
| **Jakosc kodu** | 6/10 | Czytelny Bash, ale brak walidacji wersji i brakujacy `.env.example` |
| **Funkcjonalnosc** | 5/10 | Dzialajacy happy-path, ale kruchy na edge-casach |
| **Portfolio** | 4/10 | Recruiter techiczny oczekiwalby `.env.example` i walidacji wersji |
| **Gotowosc AI** | 3/10 | Brak provisioningu dla ChromaDB/sqlite-vec/sentence-transformers |

---

## Etap 2: Pobieranie Dumpow Wikipedii

**Plik:** [fetch_sql_dumps.py](file:///home/gzyms/Dev%20Projects/WikiGraph/core/pipeline/fetch_sql_dumps.py)

### Co robi
Pobiera dumpy SQL i XML z serwerow Wikimedia Foundation. Uzywa `aria2c` dla szybkich, wielowatkowych downloadow z fallbackiem do `urllib`.

### Ocena krytyczna

**Mocne strony:**
- Fallback `aria2c` -> `urllib` to dojrzaly wzorzec operacyjny
- Poprawne konstruowanie URLi Wikimedia (`/dumps.wikimedia.org/{lang}wiki/{date}/`)
- Parametryzacja przez CLI (`--lang`, `--date`)
- Wykrywanie juz pobranych plikow (skip logic)

**Slabe strony:**
- Brak weryfikacji integralnosci pobranych plikow (Wikimedia udostepnia `sha1sums.txt` -- nie sa uzywane)
- Brak progress baru dla `urllib` fallbacku (uzytkownik nie wie, czy skrypt wisi)
- Pliki XML (`pages-articles-multistream.xml.bz2`) moga miec 5-20GB -- brak ostrzezenia o wymaganym miejscu na dysku
- Brak retry logic dla `urllib` (jedno przerwane polaczenie = porzucony download)
- Daty dumpow sa hardcodowane -- uzytkownik musi wiedziec, jaki dump jest aktualnie dostepny

### Sugestie poprawek
1. Dodac walidacje SHA1 po pobraniu (Wikimedia udostepnia hashe)
2. Implementowac `tqdm` progress bar dla fallback downloadera
3. Dodac `--latest` flag ktory automatycznie wykrywa najnowszy dump
4. Dodac retry z exponential backoff dla `urllib`

| Metryka | Ocena | Argumentacja |
|:---|:---:|:---|
| **Jakosc kodu** | 7/10 | Solidna logika z fallbackiem, czytelna struktura |
| **Funkcjonalnosc** | 6/10 | Dziala, ale brak integralnosci i retry to ryzyko operacyjne |
| **Portfolio** | 7/10 | Aria2c fallback pokazuje dojrzalosc operacyjna |
| **Gotowosc AI** | 5/10 | Trzeba dodac CirrusSearch JSON dumps jako zrodlo alternatywne |

---

## Etap 3: Ladowanie do SQLite

**Plik:** [sqlite_loader.py](file:///home/gzyms/Dev%20Projects/WikiGraph/core/loaders/sqlite_loader.py)

### Co robi
Parsuje dumpy SQL (pagelinks, page, linktarget, categorylinks) uzywajac biblioteki `mwsql` i laduje je do SQLite z optymalizacjami (WAL mode, synchronous OFF, indeksy).

### Ocena krytyczna

**Mocne strony:**
- Pragmy SQLite (`journal_mode=WAL`, `synchronous=OFF`, `cache_size=-256000`) -- to poprawne optymalizacje dla bulk-insert, pokazuja znajomosc bazy
- Obsluga encoding drift (`latin1` -> `utf-8`) w `_fix_encoding()` -- to realne rozwiazanie problemu, z ktorym borykaja sie dumpowe datasety
- Tworzenie indeksow PO zaladowaniu danych (nie przed!) -- prawidlowa kolejnosc dla wydajnosci
- Tworzenie FTS5 virtual table (`articles_fts`) -- to umozliwia wyszukiwanie pelnotekstowe

**Slabe strony:**
- `_fix_encoding()` uzywa `try/except` na kazdym wierszu bez logowania niepowodzen -- trudne do debugowania
- Brak progress bara i estymacji czasu (ladowanie milionow wierszy moze trwac godziny)
- Brak transakcji explicite -- jezeli proces umrze w polowie, baza jest w nieznanym stanie
- Rozmiar batch INSERT nie jest kontrolowany (mogloby uzywac `executemany()` z chunk size)
- Schema SQLite nie uzywa `STRICT` mode (dostepny od SQLite 3.37) -- co pozwala na ciche type coercion
- Tabela `id_mapping` jest kluczowa (mapuje `page_id` -> `qid`), ale nie ma unikalnego indeksu na `qid`

### Sugestie poprawek
1. Dodac explicit transactions z `SAVEPOINT` co N wierszy
2. Dodac `tqdm` progress bar z `total` bazowanym na rozmiarze pliku
3. Dodac unikalny indeks na `id_mapping.qid`
4. Rozwazyc `STRICT` mode dla tabel

| Metryka | Ocena | Argumentacja |
|:---|:---:|:---|
| **Jakosc kodu** | 7/10 | Dobre optymalizacje SQLite, ale brak transakcji i progressu |
| **Funkcjonalnosc** | 7/10 | Dziala poprawnie na szczesliwej sciezce |
| **Portfolio** | 8/10 | Pragmy SQLite i FTS5 robia wrazenie na technicznym interview |
| **Gotowosc AI** | 7/10 | SQLite jest gotowa baza na embeddingi (sqlite-vec) |

---

## Etap 4: Ekstrakcja Infoboxow

**Plik:** [extract_infoboxes.py](file:///home/gzyms/Dev%20Projects/WikiGraph/core/pipeline/extract_infoboxes.py)

### Co robi
Parsuje XML dump uzywajac `lxml` i `mwparserfromhell`, wyciaga infoboxy z artykulow i zapisuje je jako JSON do SQLite. Uzywa multiprocessingu i checkpointow.

### Ocena krytyczna

**Mocne strony:**
- **Quick infobox pre-check (regex)** przed odpaleniem pelnego parsera AST -- to znaczaca optymalizacja (90%+ artykulow nie ma infoboxow)
- **Multiprocessing Pool** z konfigurowalna iloscia workerow -- poprawne wykorzystanie CPU
- **System checkpointow** umozliwiajacy wznowienie po przerwaniu -- to profesjonalna cecha
- **Bulk update do tabeli tymczasowej** zamiast UPDATE po jednym wierszu -- poprawna strategia bazy

**Slabe strony:**
- `mwparserfromhell.parse()` moze rzucic niekontrolowane wyjatki na znieksztalconym wikitekscie -- widzialem ogolny `except Exception`, ale bez logowania problematycznych artykulow do pliku (trudne do post-mortem debugowania)
- **Schema Drift nie jest obsluzona** -- jak sam zauwazyles, niemieckie "infoboxy" to czesto tabele `{| class="wikitable" |}`. Ten skrypt ich nie wykryje, bo szuka tylko szablonow `{{Infoboks*}}`
- Brak limitu pamieci per-worker -- artykul o "Liscie miast" moze miec 500KB tekstu i wysadzic `mwparserfromhell`
- Dane infoboksowe sa serializowane jako surowy JSON string do kolumny TEXT -- brak walidacji schematu

### Sugestie poprawek
1. Dodac logi `bad_articles.log` z ID artykulow ktore sie nie sparsowaly
2. Dodac fallback na table-parser dla jezykow z Schema Drift (DE, IT)
3. Ograniczyc rozmiar tekstu wejsciowego per worker (np. max 200KB)
4. Rozwazyc walidacje JSON schema przed zapisem

| Metryka | Ocena | Argumentacja |
|:---|:---:|:---|
| **Jakosc kodu** | 7/10 | Solidny multiprocessing, ale brak obslugi Schema Drift |
| **Funkcjonalnosc** | 6/10 | Dziala dla PL/EN, ale nie radzi sobie z DE tabelami |
| **Portfolio** | 8/10 | Checkpoint + multiprocessing to mocna demonstracja na interview |
| **Gotowosc AI** | 6/10 | Potrzebny dodatkowy krok ekstrakcji lead section dla embeddingów |

---

## Etap 5: Generowanie CSV dla Neo4j

**Plik:** [prepare_neo4j_csv.py](file:///home/gzyms/Dev%20Projects/WikiGraph/core/pipeline/prepare_neo4j_csv.py)

### Co robi
Generuje `nodes.csv` i `edges.csv` z danych SQLite do masowego importu do Neo4j. Filtruje tylko NS=0 (artykuly), mapuje page_id na QID, i weryfikuje checksumy.

### Ocena krytyczna

**Mocne strony:**
- **Filtrowanie NS=0** -- poprawne, bo linkowanie do stron kategorii/talk pages zasmiecaloby graf
- **Checksum verification** po wygenerowaniu CSV -- profesjonalny quality gate
- **Dwuprzebiegowy algorytm** -- najpierw buduje set wezlow, potem filtruje krawedzie do istniejacych wezlow. To poprawne podejscie (brak "wiszacych krawedzi")
- **Formatowanie CSV kompatybilne z `neo4j-admin import`** (naglowki z `:ID`, `:START_ID`, `:END_ID`)

**Slabe strony:**
- Caly mapping `page_id -> qid` jest ladowany do pamieci jako dict Python -- przy 6.7M wezlow to ~2-4GB RAM. Brak ostrzezenia
- Brak deduplication edges (jesli artykul A linkuje do B dwa razy, beda dwie krawedzie)
- Brak progress bar (generowanie moze trwac 30+ minut)
- Plik nie loguje statystyk (ile wezlow/krawedzi wygenerowano, ile odrzucono)

### Sugestie poprawek
1. Dodac estymacje pamieciowa i ostrzezenie przed startem
2. Dodac deduplication krawedzi (`set()` na `(source, target)`)
3. Dodac summary log na koniec: "Generated X nodes, Y edges, rejected Z orphans"
4. Rozwazyc streaming zamiast in-memory dict dla ogromnych grafow (100M+ nodes)

| Metryka | Ocena | Argumentacja |
|:---|:---:|:---|
| **Jakosc kodu** | 7/10 | Poprawny algorytm z checksumami, ale brak memory warnings |
| **Funkcjonalnosc** | 8/10 | Generuje poprawne pliki CSV, graf importuje sie do Neo4j |
| **Portfolio** | 7/10 | Solidne, ale standardowe -- to "oczekiwany" krok w pipeline grafowym |
| **Gotowosc AI** | 8/10 | CSV gotowe, Neo4j jest fundament dla GraphRAG traversali |

---

## Etap 6: Uruchomienie Stosu (dev.sh + Docker)

**Plik:** [dev.sh](file:///home/gzyms/Dev%20Projects/WikiGraph/dev.sh)

### Co robi
Zarzadza cyklem zycia: Neo4j (Docker), FastAPI (uvicorn), Next.js frontend. Obsluguje `start/stop/restart/status` z argumentami per-komponent.

### Ocena krytyczna

**Mocne strony:**
- **Health check loop** dla backendu (curl do `/api/v1/health` z timeoutem) -- profesjonalne podejscie
- **NODE_OPTIONS="--max-old-space-size=2048"** -- to wynik realnego post-mortem (OOM na 32GB). Pokazuje dojrzalosc operacyjna
- **Automatyczny `npm install`** jesli brak `node_modules` -- wygoda dla nowego uzytkownika
- **Detekcja venv** i automatyczne uzycie sciezki venv/bin -- poprawne
- **Process kill** uzywa `pkill -f` z pattern matching -- dziala, ale ryzykowne (patrz slabe strony)

**Slabe strony:**
- `pkill -f "uvicorn app.main:app"` moze zabic inne procesy uvicorna w systemie. Powinien uzywac PID file
- `pgrep -f "next-server"` moze matchowac inne projekty Next.js. Ryzyko na maszynach developerskich
- Brak `docker-compose.yml` -- uzywa wlasnego `manage_containers.py`. To dodaje zlozonosc i utrudnia reprodukowalnosc. `docker-compose.yml` jest standardem branzy
- Frontend nie ma health checka per-endpoint (sprawdza tylko czy port odpowiada)
- Logi ida do `logs/backend.log` bez log rotation -- po kilku dniach bedzie 500MB plik

### Sugestie poprawek
1. Dodac PID file management zamiast `pkill -f`
2. Dodac `docker-compose.yml` jako alternatywe do `manage_containers.py`
3. Dodac `logrotate` konfiguracje lub limitowanie logow
4. Dodac health check dla frontendu ktory sprawdza renderowalnosc strony

| Metryka | Ocena | Argumentacja |
|:---|:---:|:---|
| **Jakosc kodu** | 7/10 | Czytelny Bash z dobrymi praktykami, ale pkill jest ryzykowne |
| **Funkcjonalnosc** | 7/10 | Dziala na dedicated dev machine, ale nie na shared environment |
| **Portfolio** | 8/10 | Health checki i OOM protection robia wrazenie |
| **Gotowosc AI** | 5/10 | Brak provisioningu dla serwisow AI (ChromaDB, model serving) |

---

## Etap 7: Backend API (FastAPI)

**Pliki:** [main.py](file:///home/gzyms/Dev%20Projects/WikiGraph/app/main.py), [neo4j_manager.py](file:///home/gzyms/Dev%20Projects/WikiGraph/app/services/neo4j_manager.py), [sqlite_service.py](file:///home/gzyms/Dev%20Projects/WikiGraph/app/services/sqlite_service.py), [ai_service.py](file:///home/gzyms/Dev%20Projects/WikiGraph/app/services/ai_service.py)

### Co robi
FastAPI serwuje RESTful API z endpointami: search, entity, graph traversal, metrics, path-finding, AI insights. Federuje zapytania do wielu instancji Neo4j (per language) i SQLite.

### Ocena krytyczna

**Mocne strony:**
- **Architektura Virtual Bridge** -- `Neo4jManager` jako Singleton z driverami per-language to inzynieryjna dojrzalosc. `query_all()` z `ThreadPoolExecutor` + `asyncio.gather()` dla rownoleglych zapytan jest poprawne
- **AIService z Strategy Pattern** -- `AIProvider` (abc) -> `MockAIProvider` / `GeminiFlashProvider`. Degradacja graceful (brak klucza API = mock). Fallback na mock przy 429 quota. To wzorcowa architektura
- **Dossier-based prompting** w `_compile_dossier()` -- zbiera metryki, topologie, similarities i infoboxy do strukturalnego kontekstu. Prompt jest precyzyjny i dobrze skomponowany
- **SQLiteService** poprawnie uzywa `run_in_executor` zeby nie blokowac async event loop (SQLite jest synchroniczny)
- **Lifespan manager** z prawidlowym zamykaniem driverow i puli polaczen

**Slabe strony:**
- **`neo4j_manager.py` linie 74-148** -- to jest potwor. 75 linii komentarzy deliberujacych o timeout implementation, ktore koncza sie na... niczym. Timeout `session.run(q, p, timeout=timeout_ms)` jest uzyty, ale developer sam w komentarzach przyznaje, ze nie wie czy dziala. To kod "work in progress" ktory trafil na produkcje
- **CORS `allow_origins=["*"]`** -- otwarte na caly swiat. Akceptowalne w dev, ale nie nadaje sie na produkcje
- **Hardcoded credentials** -- `auth=("neo4j", "wikigraph")` w `neo4j_manager.py:32`. To powinno byc w `.env`
- **Brak rate limitingu** -- kazdy moze spamowac endpointy, wlacznie z `ai/analyze` ktory wywoluje Gemini API (kosztuje pieniadze)
- **Brak API versioning strategy** -- V0 i V1 wspolzyja, ale nie ma planu deprecation
- **`SQLitePool`** -- uzywa `QueuePool`, ale SQLite w trybie WAL i tak obsluguje concurrent reads. Pool moze byc unnecessary complexity

### Sugestie poprawek
1. Wyrzucic 75 linii komentarzy z `neo4j_manager.py` i zaimplementowac timeout poprawnie (lub usunac feature)
2. Przeniesc credentials do `.env` zmiennych
3. Dodac rate limiting (`slowapi` package)
4. Dodac CORS whitelist (localhost + deployed frontend URL)
5. Usunac V0 legacy API lub dodac deprecation header

| Metryka | Ocena | Argumentacja |
|:---|:---:|:---|
| **Jakosc kodu** | 6/10 | Architektura dobra, ale neo4j_manager ma 75 linii "thinking out loud" w kodzie produkcyjnym |
| **Funkcjonalnosc** | 8/10 | API dziala, federacja wielojezyczna jest solidna, AI insights dzialaja |
| **Portfolio** | 8/10 | Virtual Bridge + Strategy Pattern + graceful degradation to silny argument |
| **Gotowosc AI** | 7/10 | Architektura jest gotowa na dodanie endpointow RAG/search. AIService latwo poszerzyc |

---

## Etap 8: Frontend (Next.js + react-force-graph-3d)

**Pliki:** [WikiNebula.tsx](file:///home/gzyms/Dev%20Projects/WikiGraph/frontend/src/components/WikiNebula.tsx) (515 lines), [NodeDetailsPanel.tsx](file:///home/gzyms/Dev%20Projects/WikiGraph/frontend/src/components/nebula/NodeDetailsPanel.tsx) (203 lines), [AIInsightCard.tsx](file:///home/gzyms/Dev%20Projects/WikiGraph/frontend/src/components/nebula/AIInsightCard.tsx)

### Co robi
3D wizualizacja grafu wiedzy z interaktywnym wyszukiwaniem, rozszerzaniem wezlow (node expansion), metrykami analitycznymi i panel AI Insights.

### Ocena krytyczna

**Mocne strony:**
- **Golden Angle Spiral layout** (`GOLDEN_ANGLE = PI * (3 - sqrt(5))`) dla rozmieszczenia klastrów jezykowych w 3D -- to jest matematycznie eleganckie i unikalne rozwiazanie. Moglbys o tym mowic godzine na interview
- **Custom force engine** -- `d3Force('lang_cluster')` dodaje wlasna sile fizyczna grupujaca wezly po jezyku. To pokazuje gleboka znajomosc `d3-force`
- **Camera fly animation** z cubiceaseuot (`1 - pow(1-t, 3)`) i custom offset kalkulacja -- to premium UX
- **Spotlight system** -- klikniecie wezla podswietla sasiadow i sciemnia reszte. Sprawna implementacja z `useMemo` na `neighbors` Set
- **NodeDetailsPanel** -- wyswietla 6 roznych metryk grafowych (PageRank, HITS Authority, Triangle Count, Louvain, Leiden, Degree) z tooltipami zawierajacymi opisy algorytmow i wzory. To jest edukacyjne i robi ogromne wrazenie wizualnie
- **AIInsightCard** -- async fetch z loading state, caching, i graceful error handling

**Slabe strony:**
- **`API_BASE = "http://localhost:8000/api/v1"`** -- hardcoded w dwoch plikach (WikiNebula.tsx:20, NodeDetailsPanel.tsx:12). To powinno byc environment variable
- **`fgRef = useRef<any>(null)`** -- `any` 4 razy w calym komponencie. W TypeScript project `any` niszczy type-safety. Nalezy uzyc wlasciwego typu z `react-force-graph-3d`
- **Search jest ograniczony do pierwszego wybranego jezyka** (`selectedLangs[0]`) -- powinien wyszukiwac rownoczesnie we wszystkich wybranych jezykach (jak robi to `query_all` w backendzie)
- **Brak error boundary** -- crash w ForceGraph3D wywali cala aplikacje (bialy ekran)
- **`handleBulkRefresh`** jest pusta (`console.log("Bulk refresh currently disabled")`) -- martwy przycisk w UI
- **No keyboard navigation** -- nie mozna uzyc Tab/Enter do nawigacji. To problem z accessibility (a11y)
- **Brak responsive design** -- panel boczny ma `w-96` (fixed 384px). Na malych ekranach sie nie zmiesci
- **`langPositionRegistry`** jest moduowym Singleton poza komponentem React -- to jest technicany dlunem (stale dane miedzy remountami), ale jest potencjalnie niebezpieczne w SSR Next.js

### Sugestie poprawek
1. Przeniesc `API_BASE` do env variable (`NEXT_PUBLIC_API_URL`)
2. Zastapic `any` wlasciwymi typami z `@types/react-force-graph`
3. Dodac `ErrorBoundary` wokolForceGraph3D
4. Wyszukiwanie multi-lang (Promise.all na wszystkich jezykach)
5. Usunac lub dokonszyc "Bulk Refresh" button
6. Dodac responsive breakpoints dla panelu bocznego

| Metryka | Ocena | Argumentacja |
|:---|:---:|:---|
| **Jakosc kodu** | 6/10 | Dobre algorytmy (Spiral, Camera Fly), ale `any` types i hardcoded URLs |
| **Funkcjonalnosc** | 7/10 | Wizulalnie imponujace, ale search jest ograniczony i sa martwe przyciski |
| **Portfolio** | 9/10 | 3D graf z custom fizyką, AI Insights, i metrykowym dashboardem -- to ZABIJA na demo |
| **Gotowosc AI** | 6/10 | AIInsightCard juz istnieje, ale potrzebny chat interface dla RAG |

---

## Etap dodatkowy: Testy

**Katalog:** [tests/](file:///home/gzyms/Dev%20Projects/WikiGraph/tests)

### Ocena krytyczna

Katalog `tests/` zawiera 8 plikow: `gate6_validation.py`, `stress_test_gate_6.py`, `master_validation_suite.py`, `master_metrics_validator.py`, `stress_test_multilang.py`, `verify_metrics_filter.py`, `check_ai_import.py`, `diagnostic_aa.py`. Sa tez podkatalogi `unit/` i `integration/`.

**Krytycznie: To nie sa testy w rozumieniu branzy.** To sa skrypty walidacyjne pisane ad-hoc. Nie uzywaja `pytest` ani `unittest`. Nie ma `conftest.py`. Nie ma `pytest.ini`. Nie ma CI/CD pipeline (GitHub Actions) ktory by je uruchamial. Nie ma pokrycia testowego (coverage).

| Metryka | Ocena | Argumentacja |
|:---|:---:|:---|
| **Jakosc kodu** | 3/10 | Skrypty ad-hoc, brak frameworka testowego |
| **Funkcjonalnosc** | 4/10 | Waliduja specyficzny stan, ale nie sa powtarzalne |
| **Portfolio** | 2/10 | Recruiter szuka pytest + GitHub Actions. To ich bedzie odstraszac |
| **Gotowosc AI** | 2/10 | Brak testow = brak siatki bezpieczenstwa przy refactorach pod AI |

> [!CAUTION]
> **To jest najslabszy punkt calego projektu.** Brak formalnych testow (`pytest`) i CI/CD jest dyskwalifikujacy na rozmowach o pozycje Mid/Regular. Naprawienie tego powinno byc priorytetem numer 1, PRZED dodawaniem jakichkolwiek funkcji AI.

---

## Podsumowanie Pipeline -- Oceny Zbiorcze

| Etap | Jakosc Kodu | Funkcjonalnosc | Portfolio | Gotowosc AI |
|:---|:---:|:---:|:---:|:---:|
| 1. Setup Environment | 6 | 5 | 4 | 3 |
| 2. Download Dumps | 7 | 6 | 7 | 5 |
| 3. SQLite Loader | 7 | 7 | 8 | 7 |
| 4. Extract Infoboxes | 7 | 6 | 8 | 6 |
| 5. Neo4j CSV | 7 | 8 | 7 | 8 |
| 6. Dev Stack (dev.sh) | 7 | 7 | 8 | 5 |
| 7. Backend API | 6 | 8 | 8 | 7 |
| 8. Frontend | 6 | 7 | 9 | 6 |
| Tests | 3 | 4 | 2 | 2 |
| **SREDNIA** | **6.2** | **6.4** | **6.8** | **5.4** |

---

# CZESC 2: OCENA GOTOWOSCI AI

## Stan obecny warstwy AI

Projekt ma juz zaczatki AI w postaci endpointu `/api/v1/ai/analyze`. Analiza tego, co jest i czego brakuje:

### Co juz jest (solidny fundament)
1. **AIService z Strategy Pattern** -- `AIProvider` -> `MockAIProvider` / `GeminiFlashProvider` z graceful degradation
2. **Dossier-based prompting** -- strukturalny kontekst z metrykami grafowymi (PageRank, HITS, Louvain, Leiden, similarities)
3. **Fallback na Mock przy quota exceeded (429)** -- system nie pada gdy skonczy sie limit API
4. **Pre-computed graph metrics w SQLite** -- PageRank, Authority, Triangle Count, Community IDs sa juz policzone i dostepne

### Co TO NIE JEST
To **nie jest RAG**. To jest "prompt stuffing" -- wrzucenie statycznych metryk do prompta i pytanie LLM o komentarz. Nie ma:
- Retrieval (wyszukiwanie dokumentow/chunkow)
- Wektorowego wyszukiwania
- Dynamicznego chodzenia po grafie
- Kontekstu z tresci artykulow

---

## Sciezka 1: Semantic Search & Vector Embeddings

### Ocena gotowosci architektury: 6/10

**Co juz masz na miejscu:**
- SQLite jako baza metadanych -- idealnie sie integruje z `sqlite-vec` (rozszerzenie SQLite dla wektorow)
- FTS5 juz dziala -- mozna zbudowac Hybrid Search (FTS5 + Vector) w jednym zapytaniu
- `extract_infoboxes.py` juz parsuje XML i wyciaga dane -- ten sam pipeline moze wyciagac lead sections
- FastAPI z `run_in_executor` juz obsluguje synchroniczne SQLite -- ten sam wzorzec zadziala dla wyszukiwania wektorowego

**Czego brakuje:**
- **Ekstrakcja czystego tekstu** (lead section) z XML dumpow -- `parser.py` musialby byc rozszerzony o `mwparserfromhell.strip_code()` z zachowaniem struktury naglowkow
- **Pipeline embeddingowy** -- nowy skrypt (`tools/ai/embed_articles.py`) ktory puszcza tekst przez `sentence-transformers`
- **Integracja sqlite-vec** -- nowa kolumna/tabela z wektorami w SQLite
- **Endpoint semantic search** -- nowy router w FastAPI

**Problem chunkingu (Twoja sluszna obawa):**
Tu sie zgadzam z Twoja intuicja -- to bedzie najtrudniejsze. Ale masz trzy opcjonalne strategie:

| Strategia | Trudnosc | Jakosc | Rekomendacja |
|:---|:---:|:---:|:---|
| CirrusSearch JSON dumps (ominijcie XML) | 3/10 | 8/10 | **NAJLEPSZA** -- czyste, pre-renderowane teksty |
| `mwparserfromhell.strip_code()` na XML | 6/10 | 6/10 | OK, ale Schema Drift nadal grozi |
| Enterprise HTML dumps -> BeautifulSoup | 5/10 | 7/10 | Dobra alternatywa |

**Estymacja czasu:** 2-4 tygodnie (z CirrusSearch: 1-2 tygodnie)
**Trudnosc implementacji:** 5/10
**Wartosc do portfolio:** 7/10

---

## Sciezka 2: GraphRAG (Text-to-Cypher)

### Ocena gotowosci architektury: 5/10

**Co juz masz na miejscu:**
- Neo4j z topologia grafu -- to jest fundament calego GraphRAG
- `Neo4jManager.query()` z async execution -- juz potrafisz wykonywac Cypher queries z FastAPI
- Schema grafu jest prosta (`:Concept` + `:LINKS_TO`) -- LLM latwo sie nauczy generowac queries
- `AIService` z providers -- mozna dodac `Text2CypherProvider`

**Czego brakuje:**
- **Bogatszy schema grafu** -- obecny schema (`:Concept` --`:LINKS_TO`--> `:Concept`) jest za prosty do zlozonych pytan. Potrzebujesz label types (:Person, :City, :Battle) albo przynajmniej property `category` na wezlach
- **Text-to-Cypher prompt engineering** -- seria promptow ktore ucza LLM schematu grafu i generowania poprawnego Cypher
- **Query validation layer** -- nie mozna wykonac byle czego co LLM wymysli. Potrzebne: whitelisting operacji (MATCH/RETURN only), timeout, result limit
- **Conversational memory** -- historia pytan w sesji
- **Chat frontend component** -- obecnie jest tylko panel metrykowy, brak interfejsu konwersacyjnego

**Krytyczna prawda o Text-to-Cypher:**
Twoj graf ma TYLKO jedna relacje (`:LINKS_TO`) i jeden label (`:Concept`). LLM nie moze napisac `MATCH (b:Battle)-[:TOOK_PLACE_IN]->(c:City)` jezeli graf nie ma typow `:Battle` ani relacji `:TOOK_PLACE_IN`. Ten przyklad ze sciezki 2 z Gemini jest **niemozliwy z obecnym schematem**. Musialbyc albo:
1. Wzbogacic schema o typy (parsing kategorii Wikipedia -> node labels) -- duzy projekt
2. Albo ograniczyc GraphRAG do pytan topologicznych ("jakie artykuly sa najblizszymi sasiadami X?", "jaka jest najkrotsza sciezka miedzy X a Y?") -- co jest realistyczne i nadal warte

**Estymacja czasu:** 4-8 tygodni (z wzbogaceniem schematu: 8-12 tygodni)
**Trudnosc implementacji:** 7/10
**Wartosc do portfolio:** 9/10

---

## Sciezka 3: GNN (Graph Neural Networks)

### Ocena gotowosci architektury: 4/10

**Co juz masz na miejscu:**
- Neo4j z miliononami wezlow i krawedzi -- dane treningowe sa gotowe
- Pre-computed features (PageRank, degree, community ID) -- moga sluzyc jako node features dla GNN
- `prepare_neo4j_csv.py` juz eksportuje graf do CSV -- mozna zmodyfikowac na format PyG

**Czego brakuje:**
- **PyTorch Geometric pipeline** -- w calosci do napisania: ladowanie grafu, tworzenie train/test split, model GCN/GAT, loop treningowy, ewaluacja
- **Feature engineering** -- node features z samych metryk grafowych to za malo. Potrzebujesz embeddingów tekstu (Sciezka 1 jest prereqiem!)
- **GPU access** -- trenowanie GNN na 6.7M wezlow wymaga GPU. Google Colab Free Tier da 15GB VRAM, co moze nie wystarczyc
- **Subgraph sampling** -- nie da sie wladowac calego grafu do GPU. Potrzebujesz GraphSAGE/ClusterGCN samplerów
- **Benchmark baseline** -- musisz porownac GNN z juz zaimplement. heurystykami (Adamic-Adar, Jaccard)
- **Endpoint inference** -- FastAPI endpoint ktory odpala model na zywo

**Estymacja czasu:** 6-12 tygodni
**Trudnosc implementacji:** 9/10
**Wartosc do portfolio:** 10/10 (ale tylko jesli jest dobrze zrobiony z benchmarkami)

---

## Rekomendowana kolejnosc implementacji

```
                  [TERAZ]                   [za 2-4 tyg]              [za 6-8 tyg]
                    |                           |                          |
     Sciezka 1: Semantic Search  --->  Sciezka 2: GraphRAG  --->  Sciezka 3: GNN
     (Embeddingi + sqlite-vec)     (Text-to-Cypher + Chat UI)   (PyTorch Geometric)
                    |                           |                          |
               prereq dla ---->           prereq dla ---->          opcjonalny
               Sciezki 2                   Sciezki 3              "cherry on top"
```

> [!IMPORTANT]
> **Zanim zaczniesz cokolwiek z AI, napraw testy.** Dodaj `pytest` z minimum 10 testami integracyjnymi (API endpoints) i skonfiguruj GitHub Actions. To zajmie 1-2 dni i drastycznie podniesie wartosc portfolio (z 2/10 na 7/10 w kategorii testow).

---

# CZESC 3: TRUDNOSC WDROZENIA I WARTOSC PORTFOLIO

## Realystyczny harmonogram

| Faza | Czas | Trudnosc | Co dostajesz |
|:---|:---:|:---:|:---|
| **Faza 0: Dlugi techniczny** | 1 tydzien | 4/10 | pytest + GitHub Actions + cleanup neo4j_manager komentarzy + .env.example |
| **Faza 1: Semantic Search** | 2-4 tygodnie | 5/10 | Embeddingi + sqlite-vec + hybrid search endpoint |
| **Faza 2: GraphRAG** | 4-6 tygodni | 7/10 | Text-to-Cypher + Chat UI + conversational memory |
| **Faza 3: GNN** | 6-10 tygodni | 9/10 | PyTorch Geometric + Link Prediction + benchmarki |
| **LACZNIE** | **3-5 miesiecy** | -- | Pelny system AI na Knowledge Graph |

## Trudnosc implementacji -- szczegolowa analiza

### Najtrudniejsze wyzwania techniczne (opinia po audycie kodu)

1. **Chunking/ekstrakcja tekstu (Trudnosc: 7/10)** -- Twoja intuicja jest poprawna. CirrusSearch JSON dumps sa obejsciem, ale wymagaja nowego loadera i nowych tabel SQLite
2. **Text-to-Cypher reliability (Trudnosc: 8/10)** -- LLM generuja bledny Cypher w ~30-40% przypadkow. Potrzebujesz retry logic, query parser, i whitelisting. To nie jest "wrzuc prompt i dziala"
3. **GNN memory management (Trudnosc: 8/10)** -- 6.7M wezlow z featureami to ~50GB danych. Wymaga subgraph sampling i zaawansowanej znajomosci PyTorch Geometric
4. **Schema drift cross-language (Trudnosc: 6/10)** -- Juz czesciowo rozwiazane przez `LanguageManager`, ale potrzebny fallback parser

### Najlatwiejsze "quick wins" (minimum wysilku, maksimum efektu)

1. **pytest + GitHub Actions (1-2 dni)** -> Portfolio +3 punkty
2. **CirrusSearch loader (2-3 dni)** -> Omija 90% problemow z XML parsowaniem
3. **sqlite-vec integracja (1-2 dni)** -> Dodaje "Vector Database" do stosu technologicznego
4. **Cleanup neo4j_manager.py (1 godzina)** -> Usun 75 linii deliberacji, zostaw czysty kod

## Wartosc do portfolio -- brutalna ocena

### Obecny stan projektu (BEZ warstwy AI)

**Ocena portfolio: 7/10**

**Argumentacja:** Projekt juz TERAZ jest ponad poziomem typowego projektu juniorskiego. Hybrid database architecture (Neo4j + SQLite), multiprocessingowy pipeline danych, 3D wizualizacja z custom fizyką, multi-language federation -- to sa cechy projektu inzynierskiego, nie projektu z bootcampu. Na rozmowe o stanowisko **Data Engineer** lub **Backend Developer** to wystarczy.

Ale na stanowisko **ML/AI Engineer** -- brakuje. Obecny endpoint `ai/analyze` to prompt-stuffing, nie prawdziwy AI.

### Po wdrozeniu Sciezki 1 (Semantic Search)

**Ocena portfolio: 8/10**

**Argumentacja:** Dodajesz do CV: "Vector embeddings pipeline", "Hybrid Search (FTS5 + semantic)", "NLP processing for 1.5M articles". To juz pozycjonuje Cie jako kandydata na **AI/ML Engineer** entry-level. Jest wystarczajace do znalezienia pracy na stanowisku **Junior/Regular AI Engineer** w firmach ktore buduja systemy wyszukiwania (e-commerce, HR-tech, legal-tech).

### Po wdrozeniu Sciezek 1+2 (Semantic Search + GraphRAG)

**Ocena portfolio: 9/10**

**Argumentacja:** To jest punkt przegieciowy. "Zaprojektowalem i wdrozylem architekture GraphRAG z Text-to-Cypher na Knowledge Graph zbudowanym z Wikipedii" -- to zdanie w CV automatycznie przenosi Cie powyzej poziomu Junior. Na rozmowie rekrutacyjnej taki system generuje 30-60 minut merytorycznej dyskusji architekturalnej. Recruiter nie bedzie mial czasu pytac o definicje pętli `while`.

### Po wdrozeniu Sciezek 1+2+3 (+ GNN)

**Ocena portfolio: 10/10**

**Argumentacja:** To jest projekt na poziomie Mid/Senior AI Engineer. GNN z Link Prediction na realnym grafie (nie zabawkowym Cora/CiteSeer) z benchmarkami vs. heurystyk -- to jest praca dyplomowa magisterska na kierunku AI. Na rynku w 2026 roku, z takim projektem i umiejetnoscia opowiedzenia o nim, nie szukasz pracy. Praca szuka Ciebie.

## Kto Cie zatrudni z takim projektem?

| Typ firmy | Stanowisko | Co ich przekona | Szansa |
|:---|:---|:---|:---:|
| **Startup AI/SaaS** | AI/ML Engineer | GraphRAG + Knowledge Graph | Wysoka |
| **Firma consultingowa** | Data Engineer / AI Engineer | Pipeline processing 6.7M nodes | Wysoka |
| **E-commerce** | Search Engineer | Hybrid Search + embeddings | Srednia |
| **Bank/fintech** | Data Engineer | Graf topology + anomaly detection potencjal | Srednia |
| **Korporacja IT (Accenture, Deloitte)** | Technical Consultant | "Zbudowalem Enterprise RAG" | Wysoka |

## Werdykt koncowy

To jest projekt, ktory **warto dokonczyc**. Fundament inzynierski (pipeline, bazy, API, frontend) jest solidny -- ocenilem go srednio na **6.8/10 dla portfolio** w obecnym stanie. Glowne braki to:

1. **Brak testow (krytyczne)** -- naprawa w 1-2 dni
2. **Brak prawdziwej warstwy AI (oczekiwane)** -- Sciezka 1 w 2-4 tygodnie
3. **Code cleanup (kosmetyczne)** -- neo4j_manager komentarze, hardcoded URLs, `any` types

Inwestycja 2-3 miesiecy pracy wznosi ten projekt z poziomu "dobry projekt studencki" (7/10) na poziom "architektura klasy Enterprise" (9/10), co na brutalnym rynku 2026 roku jest roznica miedzy "kolejne CV w stosie" a "zaproszenie na rozmowe techniczna."
