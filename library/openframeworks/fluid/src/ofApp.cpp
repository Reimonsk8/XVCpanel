#include "ofApp.h"

void ofApp::setup() {
    ofBackground(0);
    ofSetFrameRate(60);
    ofSetWindowTitle("XVCpanel — Fluid Sim (Stable Fluids)");
    ofSetWindowShape(N * 8, N * 8);

    u.assign(SIZE, 0.0f);
    v.assign(SIZE, 0.0f);
    u_prev.assign(SIZE, 0.0f);
    v_prev.assign(SIZE, 0.0f);
    dens.assign(SIZE, 0.0f);
    dens_prev.assign(SIZE, 0.0f);

    pixels.resize(N * N * 3);

    fbo.allocate(N, N, GL_RGB);
}

void ofApp::addSource(int x, int y, float dx, float dy, float amount) {
    int i = ofClamp(x * (N + 1) / ofGetWidth(), 1, N);
    int j = ofClamp(y * (N + 1) / ofGetHeight(), 1, N);
    int idx = IX(i, j);
    u[idx] += dt * dx * 500.0f;
    v[idx] += dt * dy * 500.0f;
    dens[idx] += dt * amount;
}

void ofApp::setBnd(int b, std::vector<float>& x) {
    for (int i = 1; i <= N; i++) {
        x[IX(0, i)]     = b == 1 ? -x[IX(1, i)] : x[IX(1, i)];
        x[IX(N + 1, i)] = b == 1 ? -x[IX(N, i)] : x[IX(N, i)];
        x[IX(i, 0)]     = b == 2 ? -x[IX(i, 1)] : x[IX(i, 1)];
        x[IX(i, N + 1)] = b == 2 ? -x[IX(i, N)] : x[IX(i, N)];
    }
    x[IX(0, 0)]         = 0.5f * (x[IX(1, 0)] + x[IX(0, 1)]);
    x[IX(0, N + 1)]     = 0.5f * (x[IX(1, N + 1)] + x[IX(0, N)]);
    x[IX(N + 1, 0)]     = 0.5f * (x[IX(N, 0)] + x[IX(N + 1, 1)]);
    x[IX(N + 1, N + 1)] = 0.5f * (x[IX(N, N + 1)] + x[IX(N + 1, N)]);
}

void ofApp::diffuse(int b, std::vector<float>& x, std::vector<float>& x0) {
    float a = dt * diff * N * N;
    for (int k = 0; k < 20; k++) {
        for (int i = 1; i <= N; i++) {
            for (int j = 1; j <= N; j++) {
                x[IX(i, j)] = (x0[IX(i, j)] + a * (
                    x[IX(i - 1, j)] + x[IX(i + 1, j)] +
                    x[IX(i, j - 1)] + x[IX(i, j + 1)]
                )) / (1.0f + 4.0f * a);
            }
        }
        setBnd(b, x);
    }
}

void ofApp::advect(int b, std::vector<float>& d, std::vector<float>& d0,
                   std::vector<float>& u, std::vector<float>& v) {
    float dt0 = dt * N;
    for (int i = 1; i <= N; i++) {
        for (int j = 1; j <= N; j++) {
            float x = i - dt0 * u[IX(i, j)];
            float y = j - dt0 * v[IX(i, j)];
            x = ofClamp(x, 0.5f, N + 0.5f);
            y = ofClamp(y, 0.5f, N + 0.5f);
            int i0 = (int)x, i1 = i0 + 1;
            int j0 = (int)y, j1 = j0 + 1;
            float s1 = x - i0, s0 = 1 - s1;
            float t1 = y - j0, t0 = 1 - t1;
            d[IX(i, j)] = s0 * (t0 * d0[IX(i0, j0)] + t1 * d0[IX(i0, j1)])
                         + s1 * (t0 * d0[IX(i1, j0)] + t1 * d0[IX(i1, j1)]);
        }
    }
    setBnd(b, d);
}

void ofApp::project(std::vector<float>& u, std::vector<float>& v,
                    std::vector<float>& p, std::vector<float>& div) {
    for (int i = 1; i <= N; i++) {
        for (int j = 1; j <= N; j++) {
            div[IX(i, j)] = -0.5f * (
                u[IX(i + 1, j)] - u[IX(i - 1, j)] +
                v[IX(i, j + 1)] - v[IX(i, j - 1)]
            ) / N;
            p[IX(i, j)] = 0;
        }
    }
    setBnd(0, div);
    setBnd(0, p);

    for (int k = 0; k < 20; k++) {
        for (int i = 1; i <= N; i++) {
            for (int j = 1; j <= N; j++) {
                p[IX(i, j)] = (div[IX(i, j)] +
                    p[IX(i - 1, j)] + p[IX(i + 1, j)] +
                    p[IX(i, j - 1)] + p[IX(i, j + 1)]
                ) / 4.0f;
            }
        }
        setBnd(0, p);
    }

    for (int i = 1; i <= N; i++) {
        for (int j = 1; j <= N; j++) {
            u[IX(i, j)] -= 0.5f * N * (p[IX(i + 1, j)] - p[IX(i - 1, j)]);
            v[IX(i, j)] -= 0.5f * N * (p[IX(i, j + 1)] - p[IX(i, j - 1)]);
        }
    }
    setBnd(1, u);
    setBnd(2, v);
}

void ofApp::update() {
    // auto-inject turbulence at random spots
    if (ofRandom(0, 1) < 0.3f) {
        float rx = ofRandom(1, N);
        float ry = ofRandom(1, N);
        int idx = IX((int)rx, (int)ry);
        u[idx] += ofRandom(-2, 2);
        v[idx] += ofRandom(-2, 2);
        dens[idx] += ofRandom(5, 15);
    }

    u_prev = u;
    v_prev = v;
    dens_prev = dens;

    diffuse(1, u, u_prev);
    diffuse(2, v, v_prev);
    project(u, v, u_prev, v_prev);

    u_prev = u;
    v_prev = v;
    advect(1, u, u_prev, u_prev, v_prev);
    advect(2, v, v_prev, u_prev, v_prev);
    project(u, v, u_prev, v_prev);

    diffuse(0, dens, dens_prev);
    dens_prev = dens;
    advect(0, dens, dens_prev, u, v);
}

void ofApp::draw() {
    fbo.begin();
    for (int j = 0; j < N; j++) {
        for (int i = 0; i < N; i++) {
            float d = ofClamp(dens[IX(i + 1, j + 1)], 0, 255);
            float r = d * 0.2f;
            float g = d * 0.6f;
            float b = d * 1.0f;

            ofSetColor((int)r, (int)g, (int)b);
            ofDrawRectangle(i, j, 1, 1);
        }
    }
    fbo.end();

    ofSetColor(255);
    fbo.draw(0, 0, ofGetWidth(), ofGetHeight());

    ofSetColor(255);
    ofDrawBitmapStringHighlight(
        "FPS: " + ofToString(ofGetFrameRate(), 1) + "  "
        "Grid: " + ofToString(N) + "x" + ofToString(N) + "  "
        "Click+drag to inject  |  Press C to clear",
        10, ofGetHeight() - 10
    );
}

void ofApp::mouseDragged(int x, int y, int button) {
    addSource(x, y, ofRandom(-3, 3), ofRandom(-3, 3), 200);
}

void ofApp::keyPressed(int key) {
    if (key == 'c' || key == 'C') {
        std::fill(dens.begin(), dens.end(), 0.0f);
        std::fill(u.begin(), u.end(), 0.0f);
        std::fill(v.begin(), v.end(), 0.0f);
    }
    if (key == 'f' || key == 'F') ofToggleFullscreen();
}
