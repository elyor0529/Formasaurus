# -*- coding: utf-8 -*-
from __future__ import absolute_import, division

import numpy as np
from sklearn.metrics import accuracy_score
from sklearn_crfsuite.metrics import flat_accuracy_score

from formasaurus.fieldtype_model import (
    get_realistic_form_labels,
    train,
    _PRECISE_C1_C2,
    _REALISTIC_C1_C2,
    get_Xy,
)


def test_get_realistic_formtypes(storage):
    annotations = list(storage.iter_annotations())
    y_true = [a.type_full for a in annotations]
    y_pred = get_realistic_form_labels(annotations, n_folds=5)
    score = accuracy_score(y_true, y_pred)
    assert 0.7 < score < 0.98


def test_training(storage, capsys):

    annotations = list(a for a in storage.iter_annotations(
        simplify_form_types=True,
        simplify_field_types=True,
    ) if a.fields_annotated)[:300]

    crf = train(
        annotations=annotations,
        use_precise_formtypes=False,
        optimize_hyperparameters_iters=10,
        full_form_type_names=False,
        full_field_type_names=False
    )

    out, err = capsys.readouterr()

    assert 'Training on 300 forms' in out
    assert 'realistic form types' in out
    assert 'Best hyperparameters' in out

    assert 0.0 < crf.c1 < 1.5
    assert 0.0 < crf.c2 < 0.9
    assert crf.c1, crf.c2 != _REALISTIC_C1_C2
    assert crf.c1, crf.c2 != _PRECISE_C1_C2

    form_types = np.asarray([a.type for a in annotations])
    X, y = get_Xy(annotations, form_types, full_type_names=False)
    y_pred = crf.predict(X)
    score = flat_accuracy_score(y, y_pred)
    assert 0.9 < score < 1.0  # overfitting FTW!

    field_schema = storage.get_field_schema()
    short_names = set(field_schema.types_inv.keys())
    assert set(crf.classes_).issubset(short_names)