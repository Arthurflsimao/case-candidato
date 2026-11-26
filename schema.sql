
CREATE TABLE precatorio (
    id              BIGSERIAL PRIMARY KEY,
    numero_processo VARCHAR(20) NOT NULL UNIQUE
        CHECK (numero_processo ~ '^[0-9]{20}$'),
    ente_devedor    TEXT NOT NULL,
    valor_face      NUMERIC(15,2) NOT NULL
);

CREATE TABLE pagamento (
    id              BIGSERIAL PRIMARY KEY,
    precatorio_id   BIGINT NOT NULL
        REFERENCES precatorio (id),
    evento_id       TEXT NOT NULL,
    origem          TEXT NOT NULL,
    arquivo_origem  TEXT NOT NULL,
    tipo            TEXT NOT NULL
        CHECK (tipo IN ('pagamento', 'estorno')),
    valor           NUMERIC(15,2) NOT NULL
        CHECK (valor > 0),
    pago_em         DATE NOT NULL,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uk_pagamento_origem_evento
        UNIQUE (origem, evento_id)
);

CREATE INDEX idx_pagamento_precatorio
    ON pagamento (precatorio_id);

CREATE INDEX idx_pagamento_pago_em
    ON pagamento (pago_em);