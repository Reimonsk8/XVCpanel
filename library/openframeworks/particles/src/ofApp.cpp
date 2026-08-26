#include "ofApp.h"

void ofApp::setup() {
    ofBackground(0);
    ofSetFrameRate(60);
    ofSetWindowTitle("XVCpanel — Curl Noise Particles");
    ofEnableBlendMode(OF_BLENDMODE_ADD);

    fbo.allocate(ofGetWidth(), ofGetHeight(), GL_RGBA32F);
    fbo.begin();
    ofClear(0, 0, 0, 255);
    fbo.end();

    particles.resize(NUM_PARTICLES);
    for (auto& p : particles) {
        resetParticle(p);
    }
}

void ofApp::resetParticle(Particle& p) {
    p.pos.x = ofRandom(ofGetWidth());
    p.pos.y = ofRandom(ofGetHeight());
    p.vel.set(0, 0);
    p.life = 0.0f;
    p.maxLife = ofRandom(100, 400);
    p.size = ofRandom(1.0f, 3.0f);

    float hue = ofRandom(160, 260);
    p.color = ofColor::fromHsb(hue, 180, 255, 200);
}

ofVec2f ofApp::curlNoise(ofVec2f p) {
    float eps = 0.01f;
    float n1 = ofNoise((p.x + eps) / 200.0f, p.y / 200.0f, time * 0.3f);
    float n2 = ofNoise((p.x - eps) / 200.0f, p.y / 200.0f, time * 0.3f);
    float n3 = ofNoise(p.x / 200.0f, (p.y + eps) / 200.0f, time * 0.3f);
    float n4 = ofNoise(p.x / 200.0f, (p.y - eps) / 200.0f, time * 0.3f);

    float dx = (n3 - n4) / (2.0f * eps);
    float dy = -(n1 - n2) / (2.0f * eps);

    return ofVec2f(dx, dy) * 4.0f;
}

void ofApp::update() {
    if (paused) return;

    time += ofGetLastFrameTime();
    fbo.begin();
    ofSetColor(0, 0, 0, 15);
    ofDrawRectangle(0, 0, ofGetWidth(), ofGetHeight());
    fbo.end();

    for (auto& p : particles) {
        p.life += 1.0f;
        if (p.life > p.maxLife) {
            resetParticle(p);
            continue;
        }

        ofVec2f curl = curlNoise(p.pos);
        p.vel += curl;
        p.vel *= 0.98f;
        p.pos += p.vel;

        if (p.pos.x < 0) p.pos.x = ofGetWidth();
        if (p.pos.x > ofGetWidth()) p.pos.x = 0;
        if (p.pos.y < 0) p.pos.y = ofGetHeight();
        if (p.pos.y > ofGetHeight()) p.pos.y = 0;

        float lifeRatio = p.life / p.maxLife;
        float alpha = (lifeRatio < 0.1f) ? lifeRatio * 10.0f
                    : (lifeRatio > 0.8f) ? (1.0f - lifeRatio) * 5.0f
                    : 1.0f;

        p.color.a = alpha * 180;
    }
}

void ofApp::draw() {
    fbo.draw(0, 0);

    ofEnableBlendMode(OF_BLENDMODE_ADD);
    for (auto& p : particles) {
        float lifeRatio = p.life / p.maxLife;
        float alpha = (lifeRatio < 0.1f) ? lifeRatio * 10.0f
                    : (lifeRatio > 0.8f) ? (1.0f - lifeRatio) * 5.0f
                    : 1.0f;

        ofSetColor(p.color);
        ofDrawCircle(p.pos.x, p.pos.y, p.size * alpha);
    }
    ofDisableBlendMode();

    ofSetColor(255);
    ofDrawBitmapStringHighlight(
        "FPS: " + ofToString(ofGetFrameRate(), 1) + "  "
        "Particles: " + ofToString(NUM_PARTICLES) + "  "
        "Press P to pause",
        10, ofGetHeight() - 10
    );
}

void ofApp::keyPressed(int key) {
    if (key == 'p' || key == 'P') paused = !paused;
    if (key == 'f' || key == 'F') ofToggleFullscreen();
    if (key == 'c' || key == 'C') {
        fbo.begin();
        ofClear(0, 0, 0, 255);
        fbo.end();
    }
}
