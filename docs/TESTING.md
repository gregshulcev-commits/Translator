# Тестирование

## Что покрыто

### Unit tests

- нормализация и порождение candidate forms;
- lookup в SQLite словаре;
- извлечение токенов и поиска из PDF;
- workflow «точка -> токен -> перевод».

### Integration tests

- открытие реальных загруженных PDF из текущей сессии;
- проверка, что у них есть текстовый слой и доступные слова.

### GUI smoke test

- запуск Tk GUI под `Xvfb`;
- открытие тестового PDF;
- программный «клик» по слову;
- проверка, что панель перевода обновилась.

## Как запускать

```bash
PYTHONPATH=src pytest
xvfb-run -a python3 tests/smoke_gui.py
```

## Что считается успешным результатом

- все unit tests проходят;
- smoke GUI завершился с кодом 0;
- интеграционные тесты на реальных PDF не падают.

## Что именно было проверено на реальных документах

В этой среде приложение проверялось на приложенных PDF:

- `IRIO_EPICS_Device_Driver_User's_Manual__RAJ9P8_v1_7.pdf`
- `CODAC_Core_System_Installation_Manual_33JNKW_v7_5.pdf`
- `The_CODAC_-_Plant_System_Interface_34V362_v2_2.pdf`
- `55.E2_Calibration_plan_VQXY8P_v1_0.pdf`
- `55.E2_-_H-Alpha_First_Plasma_I&C_Cubicle_57WL94_v1_0.pdf`
- `55.E2_-_H-Alpha_First_Plasma_System_I&C_SRS_57VZSU_v1_0.pdf`
- `55.E2_-_System_Detailed_Design_Descripti_57WV9W_v1_0.pdf`
- `CODAC_Core_System_Application_Developmen_33T8LW_v5_8.pdf`
- `CODAC_Core_System_Overview_34SDZ5_v7_4.pdf`

Проверялось, что:

- файлы открываются;
- количество страниц определяется корректно;
- на первой странице извлекаются слова;
- как минимум в одном из технических PDF находится слово `driver`.
