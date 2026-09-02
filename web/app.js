class NebulaForgeWeb {
    constructor() {
        this.apiBase = '/api';
        this.currentPage = 'dashboard';
        this.init();
    }

    init() {
        this.bindNavigation();
        this.loadDashboard();
    }

    bindNavigation() {
        document.querySelectorAll('.nav-item, .mobile-nav-item').forEach(item => {
            item.addEventListener('click', () => {
                const page = item.dataset.page;
                this.navigateTo(page);
            });
        });
    }

    navigateTo(page) {
        document.querySelectorAll('.nav-item, .mobile-nav-item').forEach(i => i.classList.remove('active'));
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        
        document.querySelectorAll(`[data-page="${page}"]`).forEach(el => el.classList.add('active'));
        const target = document.getElementById(`page-${page}`);
        if (target) target.classList.add('active');
        this.currentPage = page;

        switch(page) {
            case 'dashboard':
                this.loadDashboard();
                break;
            case 'projects':
                this.loadProjects();
                break;
            case 'files':
                this.loadFiles();
                break;
            case 'tunnels':
                this.loadTunnels();
                break;
            case 'viewer':
                this.initViewer();
                break;
        }
    }

    async apiCall(endpoint, method = 'GET', data = null) {
        try {
            const options = {
                method,
                headers: { 'Content-Type': 'application/json' }
            };
            if (data) options.body = JSON.stringify(data);
            
            const response = await fetch(`${this.apiBase}${endpoint}`, options);
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            return { error: error.message };
        }
    }

    async loadDashboard() {
        const stats = await this.apiCall('/stats');
        if (stats.error) return;

        document.getElementById('stat-servers').textContent = stats.servers || 0;
        document.getElementById('stat-projects').textContent = stats.projects || 0;
        document.getElementById('stat-tunnels').textContent = stats.tunnels || 0;
        document.getElementById('stat-processes').textContent = stats.processes || 0;

        await this.loadProjects();
    }

    async loadProjects() {
        const projects = await this.apiCall('/projects');
        const container = document.getElementById('all-projects');
        
        if (projects.error || !projects.length) {
            container.innerHTML = '<p class="empty-state">No projects found. Create your first project to get started.</p>';
            return;
        }

        container.innerHTML = projects.map(p => `
            <div class="project-card">
                <div class="project-header">
                    <span class="project-name">${this.escapeHtml(p.name)}</span>
                    <span class="project-status status-${p.status.toLowerCase()}">${p.status}</span>
                </div>
                <div class="project-info">
                    <div>Runtime: ${p.runtime}</div>
                    <div>Port: ${p.port}</div>
                    <div>Local: ${p.host}:${p.port}</div>
                    ${p.public_url ? `<div>Tunnel: <a href="${this.escapeHtml(p.public_url)}" target="_blank" class="tunnel-link">${this.escapeHtml(p.public_url)}</a></div>` : ''}
                </div>
                <div class="project-actions">
                    <button class="btn btn-primary" onclick="app.startProject('${p.id}')">Start</button>
                    <button class="btn" onclick="app.stopProject('${p.id}')">Stop</button>
                    <button class="btn" onclick="app.restartProject('${p.id}')">Restart</button>
                    ${p.public_url ? `<button class="btn" onclick="app.openUrl('${p.public_url}')">Open URL</button>` : ''}
                </div>
            </div>
        `).join('');
    }

    async loadFiles() {
        const files = await this.apiCall('/files');
        const tbody = document.getElementById('file-list');
        
        if (files.error || !files.length) {
            tbody.innerHTML = '<tr><td colspan="4" class="empty-state">No files to display</td></tr>';
            return;
        }

        tbody.innerHTML = files.map(f => `
            <tr>
                <td>${f.type === 'directory' ? '📁' : '📄'} ${this.escapeHtml(f.name)}</td>
                <td>${f.size || '-'}</td>
                <td>${f.modified || '-'}</td>
                <td>
                    <button class="btn" onclick="app.downloadFile('${this.escapeHtml(f.path)}')">Download</button>
                </td>
            </tr>
        `).join('');
    }

    async loadTunnels() {
        const tunnels = await this.apiCall('/tunnels');
        const container = document.getElementById('tunnels-list');
        
        if (tunnels.error || !tunnels.length) {
            container.innerHTML = '<p class="empty-state">No active tunnels.</p>';
            return;
        }

        container.innerHTML = tunnels.map(t => `
            <div class="tunnel-card">
                <div class="tunnel-header">
                    <span class="project-name">${this.escapeHtml(t.provider)}</span>
                    <span class="project-status status-${t.status.toLowerCase()}">${t.status}</span>
                </div>
                <div class="tunnel-url">${t.public_url ? this.escapeHtml(t.public_url) : 'Connecting...'}</div>
                <div class="project-actions" style="margin-top: 12px;">
                    <button class="btn" onclick="app.copyUrl('${t.public_url || ''}')">Copy URL</button>
                    <button class="btn" onclick="app.openUrl('${t.public_url || ''}')">Open</button>
                    <button class="btn btn-danger" onclick="app.stopTunnel('${t.id}')">Stop</button>
                </div>
            </div>
        `).join('');
    }

    initViewer() {
        const url = localStorage.getItem('last_viewer_url') || '';
        document.getElementById('viewer-url').value = url;
        if (url) this.loadViewer();
    }

    loadViewer() {
        const url = document.getElementById('viewer-url').value.trim();
        if (!url) return;
        
        const iframe = document.getElementById('website-frame');
        iframe.src = url;
        localStorage.setItem('last_viewer_url', url);
    }

    openInNewTab() {
        const url = document.getElementById('viewer-url').value.trim();
        if (url) window.open(url, '_blank');
    }

    async createProject() {
        const name = prompt('Project name:');
        if (!name) return;
        
        const result = await this.apiCall('/projects', 'POST', { name });
        if (result.error) {
            alert('Error: ' + result.error);
        } else {
            alert('Project created successfully!');
            this.refreshProjects();
        }
    }

    async importProject() {
        const folder = prompt('Enter project folder path:');
        if (!folder) return;
        
        const result = await this.apiCall('/projects/import', 'POST', { path: folder });
        if (result.error) {
            alert('Error: ' + result.error);
        } else {
            alert('Project imported successfully!');
            this.refreshProjects();
        }
    }

    async startProject(id) {
        const result = await this.apiCall(`/projects/${id}/start`, 'POST');
        if (result.error) {
            alert('Error: ' + result.error);
        } else {
            this.refreshProjects();
        }
    }

    async stopProject(id) {
        const result = await this.apiCall(`/projects/${id}/stop`, 'POST');
        if (result.error) {
            alert('Error: ' + result.error);
        } else {
            this.refreshProjects();
        }
    }

    async restartProject(id) {
        const result = await this.apiCall(`/projects/${id}/restart`, 'POST');
        if (result.error) {
            alert('Error: ' + result.error);
        } else {
            this.refreshProjects();
        }
    }

    async startTunnel() {
        const provider = document.getElementById('tunnel-provider').value;
        const projectId = prompt('Enter project ID (or leave empty for standalone):');
        
        const result = await this.apiCall('/tunnels', 'POST', { 
            provider,
            project_id: projectId || null
        });
        
        if (result.error) {
            alert('Error: ' + result.error);
        } else {
            alert('Tunnel started! URL: ' + (result.public_url || 'Connecting...'));
            this.loadTunnels();
        }
    }

    async stopTunnel(id) {
        const result = await this.apiCall(`/tunnels/${id}/stop`, 'POST`);
        if (result.error) {
            alert('Error: ' + result.error);
        } else {
            this.loadTunnels();
        }
    }

    refreshProjects() {
        if (this.currentPage === 'projects') {
            this.loadProjects();
        } else if (this.currentPage === 'dashboard') {
            this.loadDashboard();
        }
    }

    refreshFiles() {
        this.loadFiles();
    }

    refreshTunnels() {
        this.loadTunnels();
    }

    copyUrl(url) {
        if (!url) return;
        navigator.clipboard.writeText(url).then(() => {
            alert('URL copied to clipboard!');
        });
    }

    openUrl(url) {
        if (!url) return;
        window.open(url, '_blank');
    }

    uploadFile() {
        alert('File upload: Use the Projects page to import a folder, or use the File Manager in the desktop app.');
    }

    createFolder() {
        alert('Folder creation: Use the desktop app File Manager for full file operations.');
    }

    downloadFile(path) {
        window.open(`/api/files/download?path=${encodeURIComponent(path)}`, '_blank');
    }

    saveSettings() {
        const settings = {
            theme: document.getElementById('setting-theme').value,
            host: document.getElementById('setting-host').value,
            port: parseInt(document.getElementById('setting-port').value),
            provider: document.getElementById('setting-provider').value,
            autostart: document.getElementById('setting-autostart').checked
        };
        
        this.apiCall('/settings', 'POST', settings).then(result => {
            if (result.error) {
                alert('Error saving settings: ' + result.error);
            } else {
                alert('Settings saved successfully!');
                location.reload();
            }
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

const app = new NebulaForgeWeb();
