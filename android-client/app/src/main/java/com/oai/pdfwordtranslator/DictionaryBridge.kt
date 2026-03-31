package com.oai.pdfwordtranslator

import android.content.Context
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import org.json.JSONArray
import org.json.JSONObject

class DictionaryBridge(context: Context) {
    private val module by lazy {
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(context.applicationContext))
        }
        Python.getInstance().getModule("pdf_word_translator.mobile_api")
    }

    fun bundledAssetNames(): List<String> {
        val payload = module.callAttr("bundled_dictionary_asset_names_json").toString()
        val items = JSONArray(payload)
        return List(items.length()) { index -> items.getString(index) }
    }

    fun configureDictionaryPaths(paths: List<String>): DictionarySummary {
        val payload = module.callAttr("configure_dictionary_paths_json", JSONArray(paths).toString()).toString()
        return parseSummary(JSONObject(payload))
    }

    fun currentSummary(): DictionarySummary {
        val payload = module.callAttr("current_service_summary_json").toString()
        return parseSummary(JSONObject(payload))
    }

    fun lookupWord(word: String, direction: String): LookupPayload {
        val payload = module.callAttr("lookup_word_json", word, direction).toString()
        return parseLookup(JSONObject(payload))
    }

    private fun parseSummary(json: JSONObject): DictionarySummary {
        val configuredPaths = json.optJSONArray("configured_paths") ?: JSONArray()
        val paths = List(configuredPaths.length()) { index -> configuredPaths.getString(index) }
        return DictionarySummary(
            ok = json.optBoolean("ok", false),
            configuredPaths = paths,
            packCount = json.optInt("pack_count", 0),
            entryCount = json.optInt("entry_count", 0),
        )
    }

    private fun parseLookup(json: JSONObject): LookupPayload {
        val entryJson = json.optJSONObject("entry")
        val entry = if (entryJson == null) {
            null
        } else {
            val examplesJson = entryJson.optJSONArray("examples") ?: JSONArray()
            val examples = List(examplesJson.length()) { index ->
                val exampleJson = examplesJson.getJSONObject(index)
                ExamplePayload(
                    source = exampleJson.optString("source"),
                    target = exampleJson.optString("target"),
                )
            }
            val alternativesJson = entryJson.optJSONArray("alternative_translations") ?: JSONArray()
            val alternatives = List(alternativesJson.length()) { index -> alternativesJson.getString(index) }
            DictionaryEntryPayload(
                headword = entryJson.optString("headword"),
                bestTranslation = entryJson.optString("best_translation"),
                transcription = entryJson.optString("transcription"),
                alternativeTranslations = alternatives,
                examples = examples,
                notes = entryJson.optString("notes"),
            )
        }

        val candidatesJson = json.optJSONArray("candidate_forms") ?: JSONArray()
        val candidateForms = List(candidatesJson.length()) { index -> candidatesJson.getString(index) }

        return LookupPayload(
            ok = json.optBoolean("ok", false),
            query = json.optString("query"),
            direction = json.optString("direction"),
            strategy = json.optString("strategy"),
            error = json.optString("error"),
            candidateForms = candidateForms,
            entry = entry,
        )
    }
}

data class DictionarySummary(
    val ok: Boolean,
    val configuredPaths: List<String>,
    val packCount: Int,
    val entryCount: Int,
)

data class LookupPayload(
    val ok: Boolean,
    val query: String,
    val direction: String,
    val strategy: String,
    val error: String,
    val candidateForms: List<String>,
    val entry: DictionaryEntryPayload?,
)

data class DictionaryEntryPayload(
    val headword: String,
    val bestTranslation: String,
    val transcription: String,
    val alternativeTranslations: List<String>,
    val examples: List<ExamplePayload>,
    val notes: String,
)

data class ExamplePayload(
    val source: String,
    val target: String,
)
