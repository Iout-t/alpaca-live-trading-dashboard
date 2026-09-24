package com.ioutt.alpaca.dashboard;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.view.ViewGroup;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {
    private static final String PREFS = "dashboard";
    private static final String URL_KEY = "url";

    private WebView webView;

    @Override
    public void onCreate(Bundle state) {
        super.onCreate(state);

        String configuredUrl = BuildConfig.DASHBOARD_URL.trim();

        String savedUrl = getSharedPreferences(PREFS, MODE_PRIVATE)
                .getString(URL_KEY, "");

        String url = configuredUrl.isEmpty() ? savedUrl : configuredUrl;

        if (url.isEmpty()) {
            showUrlForm();
        } else {
            loadDashboard(normalizeUrl(url));
        }
    }

    private String normalizeUrl(String value) {
        if (!value.startsWith("https://") &&
                !value.startsWith("http://")) {
            return "https://" + value;
        }

        return value;
    }

    private void showUrlForm() {
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(40, 60, 40, 40);
        layout.setBackgroundColor(Color.rgb(16, 19, 24));

        TextView title = new TextView(this);
        title.setText("Alpaca Trading Dashboard");
        title.setTextColor(Color.WHITE);
        title.setTextSize(24);
        layout.addView(title);

        TextView help = new TextView(this);
        help.setText(
                "Enter the HTTPS URL of your deployed dashboard. " +
                "Alpaca API keys must remain on the server."
        );
        help.setTextColor(Color.LTGRAY);
        help.setPadding(0, 20, 0, 20);
        layout.addView(help);

        EditText input = new EditText(this);
        input.setHint("https://your-dashboard.example.com");
        input.setSingleLine(true);
        input.setTextColor(Color.WHITE);
        input.setHintTextColor(Color.GRAY);
        layout.addView(input);

        Button connect = new Button(this);
        connect.setText("Connect");

        connect.setOnClickListener(view -> {
            String value = input.getText().toString().trim();

            if (!value.isEmpty()) {
                getSharedPreferences(PREFS, MODE_PRIVATE)
                        .edit()
                        .putString(URL_KEY, value)
                        .apply();

                loadDashboard(normalizeUrl(value));
            }
        });

        layout.addView(connect);
        setContentView(layout);
    }

    @SuppressLint("SetJavaScriptEnabled")
    private void loadDashboard(String url) {
        webView = new WebView(this);

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(
                    WebView view,
                    WebResourceRequest request
            ) {
                return false;
            }
        });

        webView.setWebChromeClient(new WebChromeClient());

        webView.getSettings().setJavaScriptEnabled(true);
        webView.getSettings().setDomStorageEnabled(true);
        webView.getSettings().setBuiltInZoomControls(false);
        webView.getSettings().setDisplayZoomControls(false);

        webView.loadUrl(url);

        setContentView(
                webView,
                new ViewGroup.LayoutParams(-1, -1)
        );
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}