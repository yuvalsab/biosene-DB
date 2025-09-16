import logging
import json
from utils.txt_parser import extract_blocks_from_txt
from utils.lightning_loader import get_lightning_name
from utils.mongo_connector import save_document, db, Collections, bulk_save_events
from extractors.event_parser import parse_event_block
from extractors.procedure_builder import build_procedure_document


def main(json_path: str, txt_path: str):
    logging.basicConfig(
        filename="ingest.log",
        filemode="w",
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )

    # Load lightningName (JSON)
    try:
        lightning_name = get_lightning_name(json_path)
        logging.info(f"Loaded lightning_name={lightning_name}")
    except Exception as e:
        logging.error(f"Failed to load JSON file {json_path}: {e}")
        print(f"Failed to load JSON file {json_path}: {e}")
        return

    # Load full JSON for procedure doc
    try:
        with open(json_path, "r", encoding="utf-8") as fh:
            j = json.load(fh)
    except Exception as e:
        logging.error(f"Failed to parse JSON {json_path}: {e}")
        print(f"Failed to parse JSON {json_path}: {e}")
        return

    # Save procedure (to 'Procedures')
    try:
        proc_doc = build_procedure_document(j)
        proc_doc["_collection"] = Collections.Procedures
        save_document(proc_doc)
        logging.info("Saved procedure document to 'Procedures'")
    except Exception as e:
        logging.error(f"Failed to save procedure document: {e}")
        print(f"Failed to save procedure document: {e}")

    # Extract blocks from TXT
    try:
        blocks = extract_blocks_from_txt(txt_path)
        logging.info(f"Extracted {len(blocks)} blocks from TXT")
    except Exception as e:
        logging.error(f"Failed to extract blocks from TXT {txt_path}: {e}")
        print(f"Failed to extract blocks from TXT {txt_path}: {e}")
        return

    total_blocks = len(blocks)
    saved_blocks = 0
    skipped_blocks = 0
    problematic_blocks = []
    pending_events = []

    # Parse and insert relevant event blocks (interactive for unknown headers)
    for idx, block in enumerate(blocks, start=1):
        try:
            # אינטראקטיבי כמו קודם: ישאל כשלא מזהה
            doc = parse_event_block(block, lightning_name)
            if doc:
                try:
                    if doc["_collection"] == Collections.Events:
                        # נאסוף ל-bulk כדי לזרז שמירה
                        pending_events.append(doc)
                        saved_blocks += 1
                    else:
                        save_document(doc)
                        saved_blocks += 1
                except Exception as e:
                    skipped_blocks += 1
                    problematic_blocks.append({
                        "index": idx,
                        "header": block[0] if block else "EMPTY",
                        "error": str(e),
                        "doc": doc
                    })
                    logging.error(f"Failed to save block {idx}: {e}")
            else:
                skipped_blocks += 1
                logging.warning(f"Skipped block {idx}: header='{block[0] if block else 'EMPTY'}'")
        except Exception as e:
            skipped_blocks += 1
            problematic_blocks.append({
                "index": idx,
                "header": block[0] if block else "EMPTY",
                "error": str(e),
                "doc": None
            })
            logging.error(f"Failed to parse block {idx}: {e}")

    # Bulk write for Events (מהיר יותר; נפילה ל-fallback בודד במקרה חריג)
    if pending_events:
        try:
            bulk_save_events(pending_events)
        except Exception as e:
            logging.error(f"Failed bulk save events: {e}")
            for d in pending_events:
                try:
                    save_document(d)
                except Exception as ex:
                    logging.error(f"Failed fallback save for one event: {ex}")

    # Summary
    print("\n=== Summary Report ===")
    print(f"Total blocks: {total_blocks}")
    print(f"Saved: {saved_blocks}")
    print(f"Skipped: {skipped_blocks}")

    if problematic_blocks:
        print("\n⚠️ Some blocks had issues:")
        for pb in problematic_blocks:
            print(f" - Block {pb['index']}: header='{pb['header']}' → error='{pb['error']}'")

        # Ask user whether to delete problematic docs
        choice = input("\nDo you want to DELETE documents related to problematic blocks from MongoDB? (y/n): ").strip().lower()
        if choice == "y":
            for pb in problematic_blocks:
                doc = pb.get("doc")
                if not doc or "_collection" not in doc:
                    continue

                key_filter = {}
                if doc["_collection"] == Collections.Catheter:
                    key_filter = {"lightning_name": doc["lightning_name"], "catheter_ids": doc.get("catheter_ids")}
                elif doc["_collection"] == Collections.Errors:
                    key_filter = {"lightning_name": doc["lightning_name"], "error_ids": doc.get("error_ids")}
                elif doc["_collection"] == Collections.Events:
                    key_filter = {"lightning_name": doc["lightning_name"], "event_ids": doc.get("event_ids")}

                if key_filter:
                    db[doc["_collection"]].delete_many(key_filter)
                    print(f"❌ Deleted from {doc['_collection']} with filter {key_filter}")
                    logging.info(f"Deleted from {doc['_collection']} with filter {key_filter}")

    summary_msg = f"Summary: {saved_blocks}/{total_blocks} saved, {skipped_blocks} skipped"
    logging.info(summary_msg)


if __name__ == "__main__":
    print("JSON path:")
    json_file = input("JSON path: ").strip()

    print("TXT path:")
    txt_file = input("TXT path: ").strip()

    main(json_file, txt_file)
