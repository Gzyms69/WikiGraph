#!/usr/bin/env python3
import bz2
import mwxml
import mwparserfromhell

# Test mwxml with a small portion of the file
with bz2.open('raw_data_wiki/plwiki-20251201-pages-articles-multistream.xml.bz2', 'rt', encoding='utf-8') as f:
    dump = mwxml.Dump.from_file(f)
    count = 0
    for page in dump:
        print(f"Page {count+1}: {page.title} (namespace: {page.namespace})")
        print(f"  Page attributes: {dir(page)}")

        # Load revisions
        try:
            revisions = list(page)
            print(f"  Revisions loaded: {len(revisions)}")
            if revisions:
                revision = revisions[0]
                print(f"  Revision object: {revision}")
                print(f"  Revision attributes: {dir(revision)}")
                if hasattr(revision, 'text') and revision.text:
                    print(f"  Text length: {len(revision.text)}")
                    wikitext = revision.text[:500]  # First 500 chars
                    print(f"  Text preview: {wikitext[:100]}...")

                    # Test link extraction
                    wikicode = mwparserfromhell.parse(wikitext)
                    links = []
                    for link in wikicode.filter_wikilinks():
                        link_text = str(link.title).strip()
                        if ':' not in link_text and link_text:
                            links.append(link_text)
                            if len(links) >= 3:
                                break
                    print(f"  Links found: {links}")

                    # Test infobox
                    infobox = None
                    for template in wikicode.filter_templates():
                        template_name = str(template.name).strip()
                        if template_name.lower().startswith('infobox'):
                            infobox = template_name[7:].strip() if len(template_name) > 7 else template_name
                            break
                    print(f"  Infobox: {infobox}")
                else:
                    print("  No text in revision")
            else:
                print("  No revisions")
        except Exception as e:
            print(f"  Error loading revisions: {e}")

        count += 1
        if count >= 1:
            break
