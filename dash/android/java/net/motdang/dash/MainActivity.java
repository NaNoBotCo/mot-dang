package net.motdang.dash;

// One WebView holding the whole dash view. This file only opens the door, and
// three of the things it does are the difference between a demo and something
// usable on a moving bike:
//
//   KEEP_SCREEN_ON   a navigation screen that sleeps at a red light is not a
//                    navigation screen. Set for the life of the window.
//   immersive        the arrow is the product, so the system bars go away and
//                    give their height to it.
//   geolocation      granted straight through once Android has granted it to
//                    the app, because a permission prompt appearing over the
//                    arrow mid-ride is the worst possible moment for one.
//
// There is no INTERNET permission in the manifest, so there is nothing to
// sandbox here: every asset is local and the WebView has nowhere to go.

import android.Manifest;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.view.View;
import android.view.WindowManager;
import android.webkit.GeolocationPermissions;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

public class MainActivity extends Activity {
    private WebView web;
    private String geoOrigin;
    private GeolocationPermissions.Callback geoCallback;

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        getWindow().setStatusBarColor(android.graphics.Color.BLACK);
        getWindow().setNavigationBarColor(android.graphics.Color.BLACK);

        web = new WebView(this);
        web.setBackgroundColor(android.graphics.Color.BLACK);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(true);      // assets/www via file://
        s.setGeolocationEnabled(true);
        // A rider cannot pinch a screen at speed, and an accidental zoom on a
        // mount would leave the arrow half off the glass until they stopped.
        s.setSupportZoom(false);
        s.setBuiltInZoomControls(false);

        web.setWebViewClient(new WebViewClient());
        web.setWebChromeClient(new WebChromeClient() {
            @Override public void onGeolocationPermissionsShowPrompt(
                    String origin, GeolocationPermissions.Callback cb) {
                if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)
                        == PackageManager.PERMISSION_GRANTED) {
                    cb.invoke(origin, true, false);
                } else {
                    geoOrigin = origin;
                    geoCallback = cb;
                    requestPermissions(new String[]{
                        Manifest.permission.ACCESS_FINE_LOCATION,
                        Manifest.permission.ACCESS_COARSE_LOCATION}, 1);
                }
            }
        });

        setContentView(web);
        web.loadUrl("file:///android_asset/www/index.html");
    }

    private void immersive() {
        View d = getWindow().getDecorView();
        d.setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_LAYOUT_STABLE
          | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
          | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
          | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
          | View.SYSTEM_UI_FLAG_FULLSCREEN
          | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
    }

    @Override public void onWindowFocusChanged(boolean has) {
        super.onWindowFocusChanged(has);
        if (has) immersive();
    }

    @Override protected void onResume() {
        super.onResume();
        immersive();
    }

    @Override public void onRequestPermissionsResult(
            int code, String[] perms, int[] grants) {
        if (code == 1 && geoCallback != null) {
            boolean ok = false;
            for (int g : grants) if (g == PackageManager.PERMISSION_GRANTED) ok = true;
            geoCallback.invoke(geoOrigin, ok, false);
            geoCallback = null;
        }
    }
}
