package com.oai.pdfwordtranslator

import android.content.Context
import java.io.File

object AssetBootstrap {
    private const val ASSET_SUBDIR = "dictionaries"

    fun ensureBundledDictionaries(context: Context, assetNames: List<String>): List<File> {
        val targetDir = File(context.filesDir, "dictionaries")
        if (!targetDir.exists()) {
            targetDir.mkdirs()
        }

        val files = mutableListOf<File>()
        for (assetName in assetNames) {
            val targetFile = File(targetDir, assetName)
            if (!targetFile.exists()) {
                context.assets.open("$ASSET_SUBDIR/$assetName").use { input ->
                    targetFile.outputStream().use { output ->
                        input.copyTo(output)
                    }
                }
            }
            files += targetFile
        }
        return files
    }
}
