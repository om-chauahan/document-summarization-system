# UML Diagrams — AI-Powered Document Summarization System

This document contains all four UML diagrams for the project, drawn using Mermaid syntax.  
You can paste any diagram into [https://mermaid.live](https://mermaid.live) to preview and export as PNG/SVG for your report.

---

## 1. Use Case Diagram

**Actors:**
- **Guest User** — unauthenticated visitor
- **Registered User** — authenticated account holder
- **Admin** — Django superuser with backend portal access
- **Razorpay** — external payment gateway (system actor)

```mermaid
%%{init: {'theme': 'default', 'flowchart': {'curve': 'linear'}}}%%
flowchart TB
    subgraph Actors["ACTORS"]
        GU(["👤 Guest User"])
        RU(["👤 Registered User"])
        AD(["👤 Admin"])
        RP(["⚙️ Razorpay\nGateway"])
    end

    subgraph DSS["«System» Document Summarization System"]
        direction TB

        subgraph Auth["Authentication"]
            UC1["Register / Sign Up"]
            UC2["Login"]
            UC3["Logout"]
        end

        subgraph Core["Core Features"]
            UC4["Upload Document"]
            UC5["«uses» Extract Text\n(OCR / Direct)"]
            UC6["«uses» Generate Summary\n(Ollama LLM)"]
            UC7["View My Uploads"]
            UC8["Download / View Document"]
        end

        subgraph Account["Account Management"]
            UC9["Manage Profile"]
            UC10["Change Password"]
            UC11["View Security Settings"]
        end

        subgraph Billing["Credits & Billing"]
            UC12["Top-Up Credits"]
            UC13["«uses» Process Payment"]
            UC14["View Billing History"]
        end

        subgraph AdminUC["Administration"]
            UC15["Access Admin Portal"]
            UC16["Manage Users"]
            UC17["View All Documents"]
        end
    end

    GU --> UC1
    GU --> UC2

    RU --> UC2
    RU --> UC3
    RU --> UC4
    RU --> UC7
    RU --> UC8
    RU --> UC9
    RU --> UC10
    RU --> UC11
    RU --> UC12
    RU --> UC14

    AD --> UC2
    AD --> UC15
    AD --> UC16
    AD --> UC17

    UC4 -- "«include»" --> UC5
    UC4 -- "«include»" --> UC6
    UC12 -- "«include»" --> UC13
    UC13 -- "interacts" --> RP
```

---

## 2. Class Diagram

**Notes:**
- `User` is Django's built-in `AbstractUser` model.
- `UserCredits` is created automatically when a `User` is created (via `post_save` signal).
- All foreign keys and one-to-one links are shown with labelled relationships.

```mermaid
classDiagram
    direction TB

    class User {
        +int id
        +String username
        +String email
        +String password_hash
        +String first_name
        +String last_name
        +bool is_active
        +bool is_staff
        +bool is_superuser
        +DateTime date_joined
        +DateTime last_login
        ──────────────────
        +login(request)
        +logout(request)
        +set_password(raw)
        +check_password(raw) bool
    }

    class StoredDocument {
        +int id
        +int user_id FK
        +String original_name
        +String content_type
        +int size_bytes
        +String detected_type
        +BinaryField file_bytes
        +TextField extracted_text
        +TextField summary
        +DateTime created_at
        ──────────────────
        +__str__() String
    }

    class UserCredits {
        +int id
        +int user_id FK
        +int credits
        +DateTime updated_at
        ──────────────────
        +__str__() String
    }

    class RazorpayTopupOrder {
        +int id
        +int user_id FK
        +String plan_id
        +int credits_to_add
        +int amount_paise
        +String currency
        +String razorpay_order_id
        +String razorpay_payment_id
        +String status
        +DateTime created_at
        +DateTime paid_at
        ──────────────────
        +__str__() String
    }

    class SummarizationPipeline {
        <<service>>
        +summarize_document(file_bytes, filename) dict
        +extract_text(file_bytes, filename) String
        +ocr_fallback(file_bytes) String
        +call_ollama(text) dict
    }

    class OCRPipeline {
        <<service>>
        +pdf_to_text_pdfplumber(bytes) String
        +pdf_to_text_pypdf2(bytes) String
        +pdf_ocr_tesseract(bytes) String
        +image_to_text(bytes) String
        +docx_to_text(bytes) String
    }

    class RazorpayPaymentService {
        <<service>>
        +create_order(amount_paise, currency) dict
        +verify_signature(payload) bool
        +get_payment_details(payment_id) dict
    }

    User "1" --> "0..*" StoredDocument : owns
    User "1" --> "1" UserCredits : has (auto-created)
    User "1" --> "0..*" RazorpayTopupOrder : places

    SummarizationPipeline ..> OCRPipeline : uses
    SummarizationPipeline ..> User : checks credits of

    RazorpayPaymentService ..> RazorpayTopupOrder : creates/updates
```

---

## 3. Activity Diagram

### 3a. Document Upload and Summarization Flow

```mermaid
flowchart TD
    Start([🔵 User Clicks Summarize])
    --> ClientValidate{Client-Side:\nFile Type & Size OK?}

    ClientValidate -- ❌ Invalid --> ClientError([Show Validation Error in UI])
    ClientValidate -- ✅ Valid --> SendRequest

    SendRequest[POST /api/summarize/ with file]
    --> SessionCheck{Session Cookie\nValid / Authenticated?}

    SessionCheck -- ❌ Not Authenticated --> Return401([Return 401 Unauthorized])
    SessionCheck -- ✅ Authenticated --> ReadFile

    ReadFile[Read File Bytes & Detect MIME Type]
    --> TypeSwitch{File Extension /\nContent-Type?}

    TypeSwitch -- ".pdf" --> PDFDirect[Try pdfplumber: Direct Text Extraction]
    PDFDirect --> PDFCheck1{Text\nExtracted?}
    PDFCheck1 -- ✅ Yes --> Normalize
    PDFCheck1 -- ❌ No --> PyPDF2[Fallback: PyPDF2 Extraction]
    PyPDF2 --> PDFCheck2{Text\nExtracted?}
    PDFCheck2 -- ✅ Yes --> Normalize
    PDFCheck2 -- ❌ No --> PDF2Image[pdf2image: Render Pages as Images]
    PDF2Image --> Tesseract1[pytesseract: OCR Each Page Image]
    Tesseract1 --> OCRCheck{OCR Text\nFound?}
    OCRCheck -- ✅ Yes --> Normalize
    OCRCheck -- ❌ No --> ImgCaption1[Image Captioning LLM Fallback]
    ImgCaption1 --> Normalize

    TypeSwitch -- ".docx" --> DOCXExtract[python-docx: Extract Paragraphs]
    DOCXExtract --> Normalize

    TypeSwitch -- ".txt" --> TXTDecode[Decode as UTF-8 Text]
    TXTDecode --> Normalize

    TypeSwitch -- ".png/.jpg/.jpeg" --> ImgOCR[pytesseract: OCR on Image]
    ImgOCR --> ImgOCRCheck{OCR Text\nFound?}
    ImgOCRCheck -- ✅ Yes --> Normalize
    ImgOCRCheck -- ❌ No --> ImgCaption2[Image Captioning LLM Fallback]
    ImgCaption2 --> Normalize

    TypeSwitch -- "Unsupported" --> Return415([Return 415 Unsupported File Type])

    Normalize[Normalize & Clean Extracted Text]
    --> EmptyCheck{Extracted Text\nIs Empty?}
    EmptyCheck -- ❌ Empty --> Return422([Return 422 Processing Error])
    EmptyCheck -- ✅ Not Empty --> Ollama

    Ollama[Send Text Prompt to Ollama LLM]
    --> OllamaTimeout{Response Within\n60 seconds?}
    OllamaTimeout -- ❌ Timeout --> Return504([Return 504 Timeout Error])
    OllamaTimeout -- ✅ In Time --> ParseJSON

    ParseJSON[Parse LLM JSON Response\nExtract title, keywords, summary points]
    --> CalcCredits[Calculate Credit Cost\nbased on document size/type]
    CalcCredits --> CreditCheck{User Has\nSufficient Credits?}

    CreditCheck -- ❌ No --> SaveLow[Save Document with\nInsufficient Credits Notice]
    SaveLow --> ReturnLow([Return Response with Warning])

    CreditCheck -- ✅ Yes --> DeductCredits[Deduct Credits from UserCredits]
    DeductCredits --> SaveDoc[Save StoredDocument\nfile_bytes + extracted_text + summary]
    SaveDoc --> Return200([Return 200 OK: Summary + Text + Credits])

    Return200 --> DisplayUI([🟢 Frontend Displays Summary to User])
```

---

### 3b. Credit Top-Up Payment Flow

```mermaid
flowchart TD
    Start([🔵 User Selects Credit Plan])
    --> PostOrder[POST /api/create-topup-order/\n{ plan_id }]
    PostOrder --> AuthCheck{Authenticated?}
    AuthCheck -- ❌ No --> Return401([Return 401])
    AuthCheck -- ✅ Yes --> ValidPlan{Valid Plan ID?}
    ValidPlan -- ❌ No --> Return400([Return 400 Bad Request])
    ValidPlan -- ✅ Yes --> CreateRzpOrder[Call Razorpay:\nCreate Order with amount_paise]
    CreateRzpOrder --> RzpOK{Razorpay\nResponds OK?}
    RzpOK -- ❌ No --> Return502([Return 502 Payment Gateway Error])
    RzpOK -- ✅ Yes --> SaveOrder[Save RazorpayTopupOrder\nstatus = 'created']
    SaveOrder --> ReturnOrderDetails[Return order_id, key_id, amount to Frontend]
    ReturnOrderDetails --> OpenModal[Open Razorpay Checkout Modal]
    OpenModal --> UserPays{User Completes\nPayment?}
    UserPays -- ❌ Cancelled --> ShowCancelled([Show Cancellation Message])
    UserPays -- ✅ Success --> VerifyPost[POST /api/verify-topup/\n{ payment_id, order_id, signature }]
    VerifyPost --> HMACVerify{HMAC Signature\nValid?}
    HMACVerify -- ❌ Invalid --> Return400Sig([Return 400 Invalid Signature])
    HMACVerify -- ✅ Valid --> UpdateOrder[Update RazorpayTopupOrder\nstatus = 'paid', paid_at = now()]
    UpdateOrder --> AddCredits[Add credits_to_add to UserCredits]
    AddCredits --> Return200([Return 200: New Credit Balance])
    Return200 --> UpdateUI([🟢 Update Credit Display in UI])
```

---

## 4. Sequence Diagram

### 4a. Document Upload and Summarization

```mermaid
sequenceDiagram
    actor U as 👤 User
    participant F  as React Frontend
    participant DJ as Django Backend
    participant SE as Session Auth
    participant EX as Extraction Pipeline
    participant OL as Ollama LLM
    participant DB as SQLite Database

    Note over U, DB: ── Document Upload & Summarization Flow ──

    U ->> F: Select file and click "Summarize"
    F ->> F: Client-side validation (type, size)

    alt Validation fails
        F -->> U: Show validation error message
    else Validation passes
        F ->> DJ: POST /api/summarize/ (multipart, credentials: include)

        DJ ->> SE: Check session cookie
        alt Not authenticated
            SE -->> DJ: 401 Unauthorized
            DJ -->> F: 401 Unauthorized
            F -->> U: Redirect to Login
        else Authenticated
            SE -->> DJ: User object (request.user)

            DJ ->> DJ: Validate file extension & MIME type

            alt Unsupported file type
                DJ -->> F: 415 Unsupported Media Type
                F -->> U: Show file type error
            else Supported file type
                DJ ->> EX: extract_text(file_bytes, filename)

                alt PDF — embedded text
                    EX ->> EX: pdfplumber.open() → extract_text()
                else PDF — scanned / image-based
                    EX ->> EX: pdfplumber fails (no text)
                    EX ->> EX: PyPDF2 fallback → extract_text()
                    EX ->> EX: pdf2image.convert_from_bytes()
                    EX ->> EX: pytesseract.image_to_string(each page)
                else DOCX
                    EX ->> EX: python-docx → extract paragraphs
                else TXT
                    EX ->> EX: bytes.decode('utf-8')
                else PNG / JPG / JPEG
                    EX ->> EX: pytesseract.image_to_string(image)
                end

                EX -->> DJ: extracted_text (string)

                alt Extracted text is empty
                    DJ -->> F: 422 Unprocessable Entity
                    F -->> U: Show processing error
                else Text available
                    DJ ->> OL: POST /api/generate {model, prompt+text}

                    alt Ollama responds in time (< 60 s)
                        OL -->> DJ: JSON {title, keywords, summary_points}
                        DJ ->> DJ: Parse summary JSON
                        DJ ->> DB: SELECT credits WHERE user_id = ?
                        DB -->> DJ: credits balance
                        DJ ->> DB: UPDATE UserCredits SET credits = credits - cost
                        DJ ->> DB: INSERT INTO StoredDocument (file_bytes, extracted_text, summary)
                        DB -->> DJ: OK (document id)
                        DJ -->> F: 200 OK {summary, extracted_text, credits_remaining, doc_id}
                        F -->> U: Display formatted summary & key points
                    else Ollama timeout / unavailable
                        OL -->> DJ: (no response after 60 s)
                        DJ -->> F: 504 Gateway Timeout
                        F -->> U: Show "Summarization timed out" error
                    end
                end
            end
        end
    end
```

---

### 4b. User Registration and Login

```mermaid
sequenceDiagram
    actor U as 👤 User
    participant F  as React Frontend
    participant DJ as Django Backend
    participant DB as SQLite Database

    Note over U, DB: ── Registration Flow ──

    U ->> F: Fill signup form (username, email, password)
    F ->> DJ: POST /api/register/ {username, email, password}
    DJ ->> DB: SELECT * FROM auth_user WHERE username = ?
    DB -->> DJ: Empty (username available)
    DJ ->> DJ: Validate password strength
    DJ ->> DB: INSERT INTO auth_user (username, email, password_hash)
    DB -->> DJ: User ID created
    DJ ->> DB: INSERT INTO UserCredits (user_id, credits=100)
    DB -->> DJ: OK
    DJ -->> F: 201 Created {message: "Account created"}
    F -->> U: Redirect to Login page

    Note over U, DB: ── Login Flow ──

    U ->> F: Enter username and password
    F ->> DJ: POST /api/login/ {username, password}
    DJ ->> DB: SELECT * FROM auth_user WHERE username = ?
    DB -->> DJ: User record
    DJ ->> DJ: check_password(raw, hash)

    alt Invalid credentials
        DJ -->> F: 401 {error: "Invalid credentials"}
        F -->> U: Show login error
    else Valid credentials
        DJ ->> DJ: create_session(user)
        DJ -->> F: 200 OK {username, credits} + Set-Cookie: sessionid
        F ->> F: Store auth state in React context
        F -->> U: Redirect to Home / Upload page
    end
```

---

### 4c. Credit Top-Up Payment Sequence

```mermaid
sequenceDiagram
    actor U  as 👤 User
    participant F  as React Frontend
    participant DJ as Django Backend
    participant RP as Razorpay Gateway
    participant DB as SQLite Database

    Note over U, DB: ── Credit Top-Up Flow ──

    U ->> F: Click "Buy Credits" and select plan
    F ->> DJ: POST /api/create-topup-order/ {plan_id}
    DJ ->> DJ: Validate plan_id & calculate amount_paise
    DJ ->> RP: razorpay.order.create({amount, currency})
    RP -->> DJ: {id: "order_xxx", amount, currency, status: "created"}
    DJ ->> DB: INSERT INTO RazorpayTopupOrder (status='created', razorpay_order_id)
    DB -->> DJ: OK
    DJ -->> F: {razorpay_order_id, key_id, amount_paise, currency}

    F ->> U: Open Razorpay Checkout Modal (JS SDK)
    U ->> RP: Complete payment (UPI / Card / Netbanking)
    RP -->> F: {razorpay_payment_id, razorpay_order_id, razorpay_signature}

    F ->> DJ: POST /api/verify-topup/ {payment_id, order_id, signature}
    DJ ->> DJ: HMAC-SHA256 verify signature\n(key_secret + order_id + "|" + payment_id)

    alt Signature invalid
        DJ -->> F: 400 {error: "Invalid payment signature"}
        F -->> U: Show payment verification failed
    else Signature valid
        DJ ->> DB: UPDATE RazorpayTopupOrder\nSET status='paid', razorpay_payment_id=?, paid_at=NOW()
        DJ ->> DB: UPDATE UserCredits\nSET credits = credits + credits_to_add
        DB -->> DJ: OK
        DJ -->> F: 200 OK {new_balance, credits_added}
        F -->> U: Show "Credits added successfully!" + updated balance
    end
```

---

## How to Export Diagrams as Images

### Option A — Mermaid Live Editor (Easiest)
1. Go to [https://mermaid.live](https://mermaid.live)
2. Paste any `mermaid` code block above (without the triple backticks)
3. Click **Download PNG** or **Download SVG**
4. Insert the image into your Word report

### Option B — VS Code (with extension)
Install the **Mermaid Preview** extension → open this file → click the preview icon next to any diagram → right-click → **Save image**

### Option C — Pandoc (renders inline in docx)
```powershell
& "C:\Users\HP\AppData\Local\Pandoc\pandoc.exe" .\docs\UML_DIAGRAMS.md -o .\docs\UML_DIAGRAMS.docx
```
> Note: Pandoc requires the `mermaid-filter` plugin to render diagrams automatically in DOCX. Without it, the raw Mermaid code will appear as code blocks in the Word file — use Option A/B for best quality images.
