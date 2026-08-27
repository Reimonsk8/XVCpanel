// XVCpanel — Domain Warp Shader (Processing + GLSL)
PShader warpShader;

void settings() {
    size(1920, 1080, P2D);
}

void setup() {
    warpShader = loadShader("warp.glsl");
}

void draw() {
    warpShader.set("resolution", float(width), float(height));
    warpShader.set("time", millis() / 1000.0);
    shader(warpShader);
    rect(0, 0, width, height);
    resetShader();

    fill(255);
    textSize(14);
    text("FPS: " + nf(frameRate, 1, 1) + "  [F] fullscreen", 10, height - 10);
}

void keyPressed() {
    if (key == 'f' || key == 'F') {
        if (fullscreen) {
            surface.setSize(1920, 1080);
        } else {
            surface.setSize(displayWidth, displayHeight);
        }
        fullscreen = !fullscreen;
    }
}

boolean fullscreen = false;
