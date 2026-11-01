# Member 1: parser.py hisoboti

Branch: `feature/parser-cleaning`. Fayllar: `src/toyota_rag/parser.py`, `tests/test_parser.py`. Testlar o'tgan, `ruff` toza.

## Tayyor

```python
DocumentParser().parse_pdf(path, book_title, author, is_slide_deck=False) -> List[DocumentPage]
DocumentParser().clean_text(text, preserve_layout=False) -> str
DocumentParser().find_glossary_pages(pages) -> Set[int]
```

- Watermark (`Document2PDF Pilot`), `Team LiB`, `PREVIOUS NEXT`, yakka sahifa raqamlari, defis uzilishlari va ortiqcha bo'shliqlar tozalanadi.
- Qatorlar (`\n`) saqlanadi, shuning uchun chunker `["\n\n", "\n", ". ", " "]` separatorlari ishlaydi.
- `is_slide_deck=True` bo'lsa defis tuzatish va raqamli qatorlarni olib tashlash o'chiriladi, ro'yxatlar buzilmaydi.
- Bo'sh yoki o'qilmaydigan sahifalar tashlab ketiladi. `page_number` asl PDF raqami (1 dan) bo'lib qoladi, shuning uchun raqamlarda bo'shliqlar bo'ladi.

Haqiqiy kitoblarda natija:

| Kitob | Sahifa | Matnli sahifa |
|---|---|---|
| Liker, The Toyota Way | 366 | 355 |
| Ohno, TPS | 195 | 158 |

## Member 2 (chunker) uchun

1. **Ohno glossariysi 121-130-sahifada emas.** Spetsifikatsiya noto'g'ri. U PDF'ning **144-152-sahifalarida** ("Glossary of Major Terms" dan "Editor's Notes" gacha, bu 153-sahifa). Bosma raqam PDF indeksidan farq qiladi. `find_glossary_pages(pages)` buni matn bo'yicha topadi va `{144, ..., 152}` qaytaradi.
2. Glossariyda har bir termin `►` (U+25BA) belgisi bilan boshlanadi. Bu belgi kitobning boshqa joylarida ham uchraydi (masalan 15, 26-sahifalar), shuning uchun terminlarni faqat glossariy sahifalari ichida ajrating.
3. Ohno matnida so'zlar orasida tab bor edi, parser ularni bo'shliqqa almashtiradi. Ba'zi so'zlar PDF'ning o'zida bo'laklangan (`improve ment`), buni parser tuzatmaydi.
4. Ohno'da 157-179 va boshqa sahifalar rasm (matni yo'q), shuning uchun ular chunk bo'lmaydi. OCR bu vazifaga kirmagan.

## Hal qilinmagan, jamoa qaror qiladi

1. **`doc_type="glossary"` yorlig'i.** Spetsifikatsiya parserdan glossariy sahifalarini `doc_type="glossary"` bilan belgilashni talab qiladi, lekin `DocumentPage` da bunday maydon yo'q. Shartnomani men o'zgartirmadim. Variantlar:
   - `DocumentPage` ga `doc_type: str = "book"` qo'shish. Bu eski kodni buzmaydi.
   - Yoki Member 2 chunker ichida `find_glossary_pages` ni o'zi chaqiradi.

   Ayni paytda repodagi `ChunkMetadata` ham spetsifikatsiyadagi `doc_type` maydonisiz, shuning uchun u ham yangilanishi kerak.
2. **`thetoyotaway.pdf` (slayd) yo'q.** Faylni olmadim, slayd rejimi (`is_slide_deck=True`) faqat sun'iy matnda tekshirilgan. Fayl topilgach haqiqiy ishga tushirib ko'rish kerak. Chunki `pypdf` slaydlarda matn tartibini aralashtirib yuborishi mumkin.
3. **PDF joylashuvi.** Spetsifikatsiyada `data/raw/`, amalda fayllar `data/` ichida edi. Testlar ikkala joyni ham qidiradi. `config.py` dagi `RAW_DATA_DIR` esa `data/raw` ni ko'rsatadi, Member 4 buni bir xillashtirishi kerak.

## Member 4 uchun

`BOOKS_REGISTRY` dagi `"is_slides"` qiymatini `parse_pdf(..., is_slide_deck=...)` ga uzating.
