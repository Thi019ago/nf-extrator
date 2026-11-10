from decimal import Decimal

from tests.conftest import ExtratorFalso, nota_exemplo

PDF_FAKE = ("nota.pdf", b"%PDF-1.4 conteudo de teste", "application/pdf")


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_envia_nota_valida_e_salva(client, usar_extrator):
    usar_extrator(ExtratorFalso())
    r = client.post("/documentos", files={"arquivo": PDF_FAKE})
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["status"] == "processado"
    assert corpo["inconsistencias"] == []
    assert corpo["dados"]["emitente_nome"] == "Papelaria Exemplo Ltda"

    salvo = client.get(f"/documentos/{corpo['id']}").json()
    assert salvo["dados"]["valor_total"] == "35.00"


def test_nota_inconsistente_vai_para_revisao(client, usar_extrator):
    usar_extrator(ExtratorFalso(nota_exemplo(valor_total=Decimal("99.00"))))
    corpo = client.post("/documentos", files={"arquivo": PDF_FAKE}).json()
    assert corpo["status"] == "revisar"
    assert corpo["inconsistencias"]

    revisar = client.get("/documentos", params={"status": "revisar"}).json()
    assert [d["id"] for d in revisar] == [corpo["id"]]
    assert client.get("/documentos", params={"status": "processado"}).json() == []


def test_falha_na_extracao_registra_erro(client, usar_extrator):
    usar_extrator(ExtratorFalso(erro="modelo fora do ar"))
    corpo = client.post("/documentos", files={"arquivo": PDF_FAKE}).json()
    assert corpo["status"] == "erro"
    assert corpo["inconsistencias"] == ["modelo fora do ar"]


def test_rejeita_tipo_de_arquivo(client, usar_extrator):
    usar_extrator(ExtratorFalso())
    r = client.post("/documentos", files={"arquivo": ("planilha.xlsx", b"x", "application/vnd.ms-excel")})
    assert r.status_code == 415


def test_rejeita_arquivo_vazio(client, usar_extrator):
    usar_extrator(ExtratorFalso())
    r = client.post("/documentos", files={"arquivo": ("nota.pdf", b"", "application/pdf")})
    assert r.status_code == 400


def test_documento_inexistente(client):
    assert client.get("/documentos/999").status_code == 404
