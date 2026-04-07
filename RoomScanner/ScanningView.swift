//
//  ScanningView.swift
//  RoomScanner
//
//  RoomPlan scanning with compass and floor plan visualization
//

import SwiftUI
import RoomPlan
import Combine
import CoreLocation
import simd

struct ScanningView: View {
    @Environment(\.dismiss) var dismiss
    @EnvironmentObject var scanManager: ScanManager
    
    @StateObject private var captureController = RoomCaptureController()
    @StateObject private var locationManager = LocationManager()
    @State private var showingSaveDialog = false
    @State private var roomName = ""
    @State private var showingError = false
    @State private var errorMessage = ""
    @State private var showFloorPlan = true
    
    var body: some View {
        ZStack {
            // RoomPlan camera view
            RoomCaptureViewRepresentable(captureController: captureController)
                .ignoresSafeArea()
            
            // Mapping floor plan overlay
            if showFloorPlan && captureController.isScanning {
                VStack {
                    Spacer()
                    GeometryReader { geometry in
                        MappingFloorPlanView(
                            capturedRoom: captureController.capturedRoom,
                            cameraTransform: captureController.estimatedCameraPosition,
                            heading: locationManager.heading,
                            positionHistory: $captureController.positionHistory
                        )
                        .frame(height: geometry.size.height * 0.45)
                        .padding()
                    }
                }
                .ignoresSafeArea(edges: .bottom)
            }
            
            // Overlay controls
            VStack {
                // Top bar
                HStack {
                    Button(action: { dismiss() }) {
                        Image(systemName: "xmark.circle.fill")
                            .font(.title)
                            .foregroundColor(.white)
                            .padding()
                            .background(Color.black.opacity(0.5))
                            .clipShape(Circle())
                    }
                    
                    Spacer()
                    
                    // Floor plan toggle
                    if captureController.isScanning {
                        Button(action: { showFloorPlan.toggle() }) {
                            Image(systemName: showFloorPlan ? "map.fill" : "map")
                                .font(.title2)
                                .foregroundColor(.white)
                                .padding()
                                .background(Color.black.opacity(0.5))
                                .clipShape(Circle())
                        }
                    }
                    
                    Spacer()
                    
                    // Scanning status
                    if captureController.isScanning {
                        HStack {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: .white))
                            Text("Scanning...")
                                .foregroundColor(.white)
                        }
                        .padding()
                        .background(Color.black.opacity(0.5))
                        .cornerRadius(10)
                    }
                }
                .padding()
                
                Spacer()
                
                // Real-time stats
                if captureController.isScanning, let room = captureController.capturedRoom {
                    VStack(spacing: 8) {
                        HStack(spacing: 20) {
                            StatBadge(icon: "square.dashed", count: room.walls.count, label: "Walls")
                            StatBadge(icon: "door.left.hand.open", count: room.doors.count, label: "Doors")
                            StatBadge(icon: "window.vertical.open", count: room.windows.count, label: "Windows")
                            StatBadge(icon: "cube.box", count: room.objects.count, label: "Objects")
                        }
                        .padding()
                        .background(Color.black.opacity(0.7))
                        .cornerRadius(10)
                    }
                    .padding(.bottom, showFloorPlan ? 0 : 10)
                }
                
                // Bottom controls
                VStack(spacing: 20) {
                    // Instructions
                    if captureController.isScanning {
                        VStack(spacing: 8) {
                            Text("Move around the room")
                                .font(.headline)
                            if showFloorPlan {
                                Text("Watch corners align on the floor plan")
                                    .font(.subheadline)
                            } else {
                                Text("Tap map icon to see floor plan")
                                    .font(.subheadline)
                            }
                        }
                        .foregroundColor(.white)
                        .padding()
                        .background(Color.black.opacity(0.7))
                        .cornerRadius(10)
                    }
                    
                    // Control buttons
                    HStack(spacing: 40) {
                        if !captureController.isScanning {
                            Button(action: startScanning) {
                                Label("Start Scan", systemImage: "play.fill")
                                    .font(.headline)
                                    .foregroundColor(.white)
                                    .padding()
                                    .background(Color.green)
                                    .cornerRadius(10)
                            }
                        } else {
                            Button(action: stopScanning) {
                                Label("Done", systemImage: "checkmark.circle.fill")
                                    .font(.headline)
                                    .foregroundColor(.white)
                                    .padding()
                                    .background(Color.blue)
                                    .cornerRadius(10)
                            }
                        }
                    }
                    .padding(.bottom, 40)
                }
            }
        }
        .sheet(isPresented: $showingSaveDialog) {
            SaveScanView(
                roomName: $roomName,
                capturedRoom: captureController.capturedRoom,
                onSave: saveScan,
                onCancel: { showingSaveDialog = false }
            )
        }
        .alert("Error", isPresented: $showingError) {
            Button("OK") { }
        } message: {
            Text(errorMessage)
        }
        .navigationBarHidden(true)
        .onAppear {
            locationManager.startUpdating()
        }
        .onDisappear {
            locationManager.stopUpdating()
        }
    }
    
    private func startScanning() {
        captureController.startSession()
    }
    
    private func stopScanning() {
        captureController.stopSession()
        showingSaveDialog = true
    }
    
    private func saveScan() {
        guard let capturedRoom = captureController.capturedRoom else {
            errorMessage = "No scan data available"
            showingError = true
            return
        }
        
        Task {
            do {
                try await scanManager.addScan(name: roomName, capturedRoom: capturedRoom)
                dismiss()
            } catch {
                errorMessage = error.localizedDescription
                showingError = true
            }
        }
    }
}

// MARK: - Stat Badge Component

struct StatBadge: View {
    let icon: String
    let count: Int
    let label: String
    
    var body: some View {
        VStack(spacing: 4) {
            Image(systemName: icon)
                .font(.system(size: 16))
            Text("\(count)")
                .font(.system(size: 18, weight: .bold))
                .monospacedDigit()
            Text(label)
                .font(.system(size: 10))
        }
        .foregroundColor(.white)
        .frame(width: 70)
    }
}

// MARK: - Location Manager for Compass

class LocationManager: NSObject, ObservableObject, CLLocationManagerDelegate {
    private let manager = CLLocationManager()
    @Published var heading: CLLocationDirection?
    
    override init() {
        super.init()
        manager.delegate = self
    }
    
    func startUpdating() {
        manager.requestWhenInUseAuthorization()
        if CLLocationManager.headingAvailable() {
            manager.startUpdatingHeading()
        }
    }
    
    func stopUpdating() {
        manager.stopUpdatingHeading()
    }
    
    func locationManager(_ manager: CLLocationManager, didUpdateHeading newHeading: CLHeading) {
        if newHeading.headingAccuracy >= 0 {
            DispatchQueue.main.async {
                self.heading = newHeading.trueHeading >= 0 ? newHeading.trueHeading : newHeading.magneticHeading
            }
        }
    }
}

// MARK: - RoomCapture Controller

class RoomCaptureController: NSObject, ObservableObject, RoomCaptureSessionDelegate {
    @Published var isScanning = false
    @Published var capturedRoom: CapturedRoom?
    @Published var estimatedCameraPosition: simd_float4x4?
    @Published var positionHistory: [simd_float3] = []
    
    private var roomSession: RoomCaptureSession?
    private var lastPositionUpdate = Date()
    
    func startSession() {
        let session = RoomCaptureSession()
        session.delegate = self
        
        let config = RoomCaptureSession.Configuration()
        session.run(configuration: config)
        
        roomSession = session
        isScanning = true
        positionHistory.removeAll()
    }
    
    func stopSession() {
        roomSession?.stop()
        isScanning = false
    }
    
    // MARK: - RoomCaptureSessionDelegate
    
    func captureSession(_ session: RoomCaptureSession, didUpdate room: CapturedRoom) {
        DispatchQueue.main.async {
            self.capturedRoom = room
            
            // Estimate camera position from room geometry
            // Since we can't access ARSession directly, we'll estimate based on room center
            if !room.walls.isEmpty {
                // Calculate room center
                var centerX: Float = 0
                var centerY: Float = 0
                var centerZ: Float = 0
                
                for wall in room.walls {
                    centerX += Float(wall.transform.columns.3.x)
                    centerY += Float(wall.transform.columns.3.y)
                    centerZ += Float(wall.transform.columns.3.z)
                }
                
                let count = Float(room.walls.count)
                centerX /= count
                centerY /= count
                centerZ /= count
                
                // Create estimated camera transform at room center
                var transform = matrix_identity_float4x4
                transform.columns.3 = simd_float4(centerX, centerY, centerZ, 1.0)
                self.estimatedCameraPosition = transform
                
                // Add to history periodically
                let now = Date()
                if now.timeIntervalSince(self.lastPositionUpdate) >= 0.2 {
                    let position = simd_float3(centerX, centerY, centerZ)
                    self.positionHistory.append(position)
                    self.lastPositionUpdate = now
                    
                    // Limit history
                    if self.positionHistory.count > 200 {
                        self.positionHistory.removeFirst()
                    }
                }
            }
        }
    }
    
    func captureSession(_ session: RoomCaptureSession, didEndWith data: CapturedRoomData, error: Error?) {
        if let error = error {
            print("Capture session error: \(error.localizedDescription)")
            return
        }
        
        DispatchQueue.main.async {
            self.isScanning = false
        }
    }
}

// MARK: - RoomCaptureView Representable

struct RoomCaptureViewRepresentable: UIViewRepresentable {
    @ObservedObject var captureController: RoomCaptureController
    
    func makeUIView(context: Context) -> RoomCaptureView {
        let captureView = RoomCaptureView(frame: .zero)
        return captureView
    }
    
    func updateUIView(_ uiView: RoomCaptureView, context: Context) {
        // RoomCaptureView automatically connects to active sessions
    }
}

// MARK: - Save Dialog

struct SaveScanView: View {
    @Binding var roomName: String
    let capturedRoom: CapturedRoom?
    let onSave: () -> Void
    let onCancel: () -> Void
    
    var body: some View {
        NavigationView {
            Form {
                Section {
                    TextField("Room name", text: $roomName)
                } header: {
                    Text("Save Scan")
                }
                
                if let room = capturedRoom {
                    Section {
                        HStack {
                            Text("Walls")
                            Spacer()
                            Text("\(room.walls.count)")
                                .foregroundColor(.secondary)
                        }
                        HStack {
                            Text("Doors")
                            Spacer()
                            Text("\(room.doors.count)")
                                .foregroundColor(.secondary)
                        }
                        HStack {
                            Text("Windows")
                            Spacer()
                            Text("\(room.windows.count)")
                                .foregroundColor(.secondary)
                        }
                        HStack {
                            Text("Objects")
                            Spacer()
                            Text("\(room.objects.count)")
                                .foregroundColor(.secondary)
                        }
                    } header: {
                        Text("Detected Elements")
                    }
                }
            }
            .navigationTitle("Save Scan")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        onCancel()
                    }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") {
                        onSave()
                    }
                    .disabled(roomName.isEmpty)
                }
            }
        }
    }
}
