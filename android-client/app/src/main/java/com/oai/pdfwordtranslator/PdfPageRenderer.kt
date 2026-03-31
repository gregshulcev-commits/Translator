package com.oai.pdfwordtranslator

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.Matrix
import android.graphics.pdf.PdfRenderer
import android.net.Uri
import android.os.ParcelFileDescriptor
import kotlin.math.max
import kotlin.math.roundToInt

class PdfPageRenderer {
    private var fileDescriptor: ParcelFileDescriptor? = null
    private var renderer: PdfRenderer? = null

    fun open(context: Context, uri: Uri) {
        close()
        val descriptor = context.contentResolver.openFileDescriptor(uri, "r")
            ?: throw IllegalStateException("Не удалось открыть PDF")
        fileDescriptor = descriptor
        renderer = PdfRenderer(descriptor)
    }

    fun pageCount(): Int = renderer?.pageCount ?: 0

    fun renderPage(pageIndex: Int, requestedWidthPx: Int): Bitmap {
        val renderer = renderer ?: throw IllegalStateException("PDF не открыт")
        require(pageIndex in 0 until renderer.pageCount) { "Недопустимый индекс страницы: $pageIndex" }

        val page = renderer.openPage(pageIndex)
        try {
            val safeWidth = max(requestedWidthPx, 720)
            val scale = safeWidth.toFloat() / page.width.toFloat()
            val bitmap = Bitmap.createBitmap(
                (page.width * scale).roundToInt(),
                (page.height * scale).roundToInt(),
                Bitmap.Config.ARGB_8888,
            )
            bitmap.eraseColor(Color.WHITE)
            val matrix = Matrix().apply { postScale(scale, scale) }
            page.render(bitmap, null, matrix, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
            return bitmap
        } finally {
            page.close()
        }
    }

    fun close() {
        renderer?.close()
        renderer = null
        fileDescriptor?.close()
        fileDescriptor = null
    }
}
