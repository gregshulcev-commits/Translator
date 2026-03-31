package com.oai.pdfwordtranslator

import android.content.Intent
import android.graphics.Bitmap
import android.net.Uri
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.ImageView
import android.widget.RadioButton
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class MainActivity : AppCompatActivity() {
    private lateinit var dictionaryBridge: DictionaryBridge
    private val pdfRenderer = PdfPageRenderer()
    private val executor: ExecutorService = Executors.newSingleThreadExecutor()

    private lateinit var statusText: TextView
    private lateinit var pageInfoText: TextView
    private lateinit var pdfImage: ImageView
    private lateinit var lookupInput: EditText
    private lateinit var lookupHeadwordText: TextView
    private lateinit var lookupBestTranslationText: TextView
    private lateinit var lookupAlternativesText: TextView
    private lateinit var lookupExamplesText: TextView
    private lateinit var radioEnRu: RadioButton
    private lateinit var radioRuEn: RadioButton

    private var currentPdfUri: Uri? = null
    private var currentPageIndex: Int = 0

    private val openPdfDocument = registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) {
            try {
                contentResolver.takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION)
            } catch (_: SecurityException) {
                // Not every provider grants persistable permissions; runtime access is still enough.
            }
            openPdf(uri)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        statusText = findViewById(R.id.textStatus)
        pageInfoText = findViewById(R.id.textPageInfo)
        pdfImage = findViewById(R.id.imagePdfPage)
        lookupInput = findViewById(R.id.editLookupWord)
        lookupHeadwordText = findViewById(R.id.textLookupHeadword)
        lookupBestTranslationText = findViewById(R.id.textLookupBestTranslation)
        lookupAlternativesText = findViewById(R.id.textLookupAlternatives)
        lookupExamplesText = findViewById(R.id.textLookupExamples)
        radioEnRu = findViewById(R.id.radioEnRu)
        radioRuEn = findViewById(R.id.radioRuEn)

        dictionaryBridge = DictionaryBridge(this)
        bootstrapBundledDictionaries()

        findViewById<Button>(R.id.buttonOpenPdf).setOnClickListener {
            openPdfDocument.launch(arrayOf("application/pdf"))
        }
        findViewById<Button>(R.id.buttonPrevPage).setOnClickListener {
            if (currentPageIndex > 0) {
                currentPageIndex -= 1
                renderCurrentPage()
            }
        }
        findViewById<Button>(R.id.buttonNextPage).setOnClickListener {
            if (currentPageIndex + 1 < pdfRenderer.pageCount()) {
                currentPageIndex += 1
                renderCurrentPage()
            }
        }
        findViewById<Button>(R.id.buttonLookup).setOnClickListener {
            runDictionaryLookup()
        }
    }

    private fun bootstrapBundledDictionaries() {
        statusText.text = getString(R.string.status_bootstrap)
        executor.execute {
            runCatching {
                val assets = dictionaryBridge.bundledAssetNames()
                val copiedFiles = AssetBootstrap.ensureBundledDictionaries(this, assets)
                dictionaryBridge.configureDictionaryPaths(copiedFiles.map { it.absolutePath })
            }.onSuccess { summary ->
                runOnUiThread {
                    statusText.text = "Словари готовы: ${summary.packCount} пак., ${summary.entryCount} entries"
                }
            }.onFailure { error ->
                runOnUiThread {
                    statusText.text = "Ошибка инициализации словарей: ${error.message}"
                }
            }
        }
    }

    private fun openPdf(uri: Uri) {
        statusText.text = "Открываю PDF…"
        currentPdfUri = uri
        currentPageIndex = 0
        executor.execute {
            runCatching {
                pdfRenderer.open(this, uri)
                pdfRenderer.pageCount()
            }.onSuccess { pageCount ->
                runOnUiThread {
                    statusText.text = "PDF открыт: $pageCount стр."
                    renderCurrentPage()
                }
            }.onFailure { error ->
                runOnUiThread {
                    statusText.text = "Не удалось открыть PDF: ${error.message}"
                    pageInfoText.text = getString(R.string.no_pdf_loaded)
                }
            }
        }
    }

    private fun renderCurrentPage() {
        val uri = currentPdfUri ?: return
        statusText.text = "Рендер страницы ${currentPageIndex + 1}…"
        executor.execute {
            runCatching {
                val width = maxOf(resources.displayMetrics.widthPixels - (resources.displayMetrics.density * 48).toInt(), 720)
                pdfRenderer.renderPage(currentPageIndex, width)
            }.onSuccess { bitmap: Bitmap ->
                runOnUiThread {
                    pdfImage.setImageBitmap(bitmap)
                    pageInfoText.text = "${currentPageIndex + 1} / ${pdfRenderer.pageCount()} • ${uri.lastPathSegment ?: "PDF"}"
                    statusText.text = "PDF готов. Для словаря введите слово вручную ниже."
                }
            }.onFailure { error ->
                runOnUiThread {
                    statusText.text = "Ошибка рендера PDF: ${error.message}"
                }
            }
        }
    }

    private fun runDictionaryLookup() {
        val query = lookupInput.text?.toString()?.trim().orEmpty()
        if (query.isBlank()) {
            statusText.text = getString(R.string.lookup_empty)
            return
        }
        val direction = if (radioRuEn.isChecked) "ru-en" else "en-ru"
        statusText.text = "Ищу перевод…"
        executor.execute {
            runCatching {
                dictionaryBridge.lookupWord(query, direction)
            }.onSuccess { result ->
                runOnUiThread {
                    applyLookupResult(result)
                }
            }.onFailure { error ->
                runOnUiThread {
                    statusText.text = "Ошибка lookup: ${error.message}"
                }
            }
        }
    }

    private fun applyLookupResult(result: LookupPayload) {
        if (!result.ok || result.entry == null) {
            lookupHeadwordText.text = result.query
            lookupBestTranslationText.text = getString(R.string.lookup_not_found)
            lookupAlternativesText.text = if (result.candidateForms.isNotEmpty()) {
                "Проверенные формы: ${result.candidateForms.joinToString()}"
            } else {
                result.error
            }
            lookupExamplesText.text = ""
            statusText.text = if (result.error.isNotBlank()) {
                "Ошибка lookup: ${result.error}"
            } else {
                getString(R.string.lookup_not_found)
            }
            return
        }

        val entry = result.entry
        lookupHeadwordText.text = buildString {
            append(entry.headword)
            if (entry.transcription.isNotBlank()) {
                append("   [")
                append(entry.transcription)
                append(']')
            }
        }
        lookupBestTranslationText.text = entry.bestTranslation
        lookupAlternativesText.text = if (entry.alternativeTranslations.isNotEmpty()) {
            "Альтернативы: ${entry.alternativeTranslations.joinToString()}"
        } else {
            entry.notes
        }
        lookupExamplesText.text = if (entry.examples.isNotEmpty()) {
            entry.examples.joinToString("\n\n") { example ->
                "${example.source}\n${example.target}"
            }
        } else {
            entry.notes
        }
        statusText.text = "Перевод найден (${if (radioEnRu.isChecked) "EN → RU" else "RU → EN"})."
    }

    override fun onDestroy() {
        super.onDestroy()
        pdfRenderer.close()
        executor.shutdownNow()
    }
}
