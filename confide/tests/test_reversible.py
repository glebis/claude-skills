import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))
import confide_core as C

P = C.make_placeholder  # P("PERSON",1) -> "[CONFIDE_PERSON_0001]"

def _spans(text, vals_types):
    sp=[]
    for v,t in vals_types:
        i=text.find(v)
        while i!=-1: sp.append(C.Span(i,i+len(v),v,t,"x")); i=text.find(v,i+1)
    return sp

def test_unique_coreferent_placeholders():
    t="Marina met Marina and Igor on 15.01."
    green,m=C.redact_reversible(t,_spans(t,[("Marina","PERSON"),("Igor","PERSON")]))
    flat=C.map_lookup(m)
    assert green.count(P("PERSON",1))==2          # same value -> same placeholder (coref)
    assert P("PERSON",2) in green                  # distinct person -> new placeholder
    assert "Marina" not in green and "Igor" not in green
    assert flat[P("PERSON",1)]=="Marina" and flat[P("PERSON",2)]=="Igor"

def test_map_has_originals_green_does_not():
    t="email a@b.io here"
    green,m=C.redact_reversible(t,_spans(t,[("a@b.io","EMAIL")]))
    flat=C.map_lookup(m)
    assert "a@b.io" not in green and "a@b.io" in flat[P("EMAIL",1)]

def test_map_is_structured_schema():
    t="email a@b.io here"
    green,m=C.redact_reversible(t,_spans(t,[("a@b.io","EMAIL")]))
    assert m["schema_version"]==C.MAP_SCHEMA_VERSION
    assert m["green_sha256"]==C.green_sha256(green)
    assert m["doc_id"] and m["created"]
    e=m["entries"][0]
    assert e["placeholder"]==P("EMAIL",1) and e["type"]=="EMAIL" and e["original"]=="a@b.io"

def test_rehydrate_exact_roundtrip():
    t="Marina and Igor"
    green,m=C.redact_reversible(t,_spans(t,[("Marina","PERSON"),("Igor","PERSON")]))
    back,stats=C.rehydrate(green,m)
    assert back==t and stats["unmatched"]==0 and stats["restored"]==2

def test_rehydrate_handles_mangled_placeholders():
    # mangled variants must STILL contain the full CONFIDE_TYPE_NNNN core
    m={P("PERSON",1):"Marina", P("DATE",1):"15 January"}
    analysis=("The client (CONFIDE PERSON 0001) felt anxious about [CONFIDE_DATE_0001]; "
              "confide_person_0001 recurred.")
    back,stats=C.rehydrate(analysis,m)
    assert "Marina" in back and "15 January" in back
    assert "CONFIDE" not in back.upper()
    assert stats["restored"]>=3

def test_rehydrate_no_cross_number_corruption():
    m={P("PERSON",1):"Ann", P("PERSON",10):"Bob"}
    back,_=C.rehydrate(f"{P('PERSON',10)} knows {P('PERSON',1)}",m)
    assert back=="Bob knows Ann"   # _0001 must not eat _0010

def test_rehydrate_reports_unmatched():
    back,stats=C.rehydrate(f"hi {P('PERSON',9)} there",{P("PERSON",1):"Marina"})
    assert stats["unmatched"]==1 and P("PERSON",9) in back
