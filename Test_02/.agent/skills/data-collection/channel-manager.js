/**
 * 증권 관련 텔레그램 채널 관리 모듈
 * 주요 증권 채널 목록을 관리하고 모니터링 설정
 */

class ChannelManager {
    constructor() {
        this.channels = new Map();
        this.categories = new Map();
        this.initializeDefaultChannels();
    }

    /**
     * 기본 증권 채널 초기화
     */
    initializeDefaultChannels() {
        const defaultChannels = {
            'major_brokers': [
                {
                    id: '@miraeasset_news',
                    name: '미래에셋증권',
                    description: '미래에셋증권 공식 채널',
                    category: 'broker',
                    priority: 'high',
                    keywords: ['미래에셋', '리서치', '투자전략']
                },
                {
                    id: '@kiwoom_news',
                    name: '키움증권',
                    description: '키움증권 공식 채널',
                    category: 'broker',
                    priority: 'high',
                    keywords: ['키움', '영업이익', '증권사']
                },
                {
                    id: '@shinhan_news',
                    name: '신한투자증권',
                    description: '신한투자증권 공식 채널',
                    category: 'broker',
                    priority: 'high',
                    keywords: ['신한', '투자전략', '시장전망']
                }
            ],
            'news_media': [
                {
                    id: '@maekyung_economy',
                    name: '매일경제',
                    description: '매일경제 경제 뉴스',
                    category: 'news',
                    priority: 'high',
                    keywords: ['경제', '증시', '기업']
                },
                {
                    id: '@hankyung_economy',
                    name: '한국경제',
                    description: '한국경제 경제 뉴스',
                    category: 'news',
                    priority: 'high',
                    keywords: ['경제', '산업', '투자']
                },
                {
                    id: '@munhwa_economy',
                    name: '문화일보 경제',
                    description: '문화일보 경제 섹션',
                    category: 'news',
                    priority: 'medium',
                    keywords: ['경제', '증권', '시장']
                }
            ],
            'stock_communities': [
                {
                    id: '@stock_master_kr',
                    name: '주식 마스터',
                    description: '주식 정보 공유 커뮤니티',
                    category: 'community',
                    priority: 'medium',
                    keywords: ['주식', '종목', '분석']
                },
                {
                    id: '@korea_stock_info',
                    name: '한국 주식 정보',
                    description: '국내 주식 정보 제공',
                    category: 'community',
                    priority: 'medium',
                    keywords: ['코스피', '코스닥', '주식']
                },
                {
                    id: '@investment_korea',
                    name: '투자 Korea',
                    description: '투자 정보 및 분석',
                    category: 'community',
                    priority: 'medium',
                    keywords: ['투자', '분석', '전략']
                }
            ],
            'sector_specific': [
                {
                    id: '@semiconductor_kr',
                    name: '반도체 동향',
                    description: '반도체 산업 뉴스 및 분석',
                    category: 'sector',
                    priority: 'medium',
                    keywords: ['반도체', '삼성전자', 'SK하이닉스', '메모리']
                },
                {
                    id: '@bio_stocks_kr',
                    name: '바이오 주식',
                    description: '바이오/의약품 주식 정보',
                    category: 'sector',
                    priority: 'medium',
                    keywords: ['바이오', '셀트리온', '신약', '임상']
                },
                {
                    id: '@it_tech_stocks',
                    name: 'IT/테크 주식',
                    description: 'IT 기술주 정보 및 분석',
                    category: 'sector',
                    priority: 'medium',
                    keywords: ['IT', '테크', '플랫폼', 'AI']
                }
            ],
            'international': [
                {
                    id: '@wall_street_kr',
                    name: '월스트리트 한국',
                    description: '미국 증시 정보 및 분석',
                    category: 'international',
                    priority: 'low',
                    keywords: ['뉴욕', '나스닥', 'S&P', '미국주식']
                },
                {
                    id: '@global_markets',
                    name: '글로벌 마켓',
                    description: '글로벌 시장 동향 분석',
                    category: 'international',
                    priority: 'low',
                    keywords: ['글로벌', '해외주식', '환율']
                }
            ],
            'real_time': [
                {
                    id: '@korea_stock_realtime',
                    name: '국내 주식 실시간',
                    description: '국내 주식 실시간 소식',
                    category: 'realtime',
                    priority: 'high',
                    keywords: ['실시간', '코스피', '거래량', '급등락']
                },
                {
                    id: '@stock_signals_kr',
                    name: '주식 시그널',
                    description: '주식 투자 시그널 제공',
                    category: 'realtime',
                    priority: 'medium',
                    keywords: ['시그널', '매수', '매도', '타이밍']
                }
            ]
        };

        // 채널 등록
        Object.entries(defaultChannels).forEach(([category, channelList]) => {
            this.addCategory(category, {
                name: this.getCategoryName(category),
                description: this.getCategoryDescription(category)
            });
            
            channelList.forEach(channel => {
                this.addChannel(channel.id, {
                    ...channel,
                    category,
                    addedAt: new Date(),
                    isActive: true,
                    lastChecked: null,
                    messageCount: 0
                });
            });
        });
    }

    /**
     * 카테고리명 가져오기
     */
    getCategoryName(category) {
        const names = {
            major_brokers: '주요 증권사',
            news_media: '뉴스 미디어',
            stock_communities: '주식 커뮤니티',
            sector_specific: '특정 섹터',
            international: '해외 증시',
            real_time: '실시간 정보'
        };
        return names[category] || category;
    }

    /**
     * 카테고리 설명 가져오기
     */
    getCategoryDescription(category) {
        const descriptions = {
            major_brokers: '국내 주요 증권사 공식 채널',
            news_media: '경제/증시 관련 뉴스 미디어',
            stock_communities: '주식 정보 공유 커뮤니티',
            sector_specific: '특정 산업/섹터 전문 채널',
            international: '해외 증시 및 글로벌 시장',
            real_time: '실시간 주식 정보 및 시그널'
        };
        return descriptions[category] || '';
    }

    /**
     * 채널 추가
     */
    addChannel(channelId, channelInfo) {
        this.channels.set(channelId, {
            id: channelId,
            name: channelInfo.name || channelId,
            description: channelInfo.description || '',
            category: channelInfo.category || 'other',
            priority: channelInfo.priority || 'medium',
            keywords: channelInfo.keywords || [],
            addedAt: channelInfo.addedAt || new Date(),
            isActive: channelInfo.isActive !== false,
            lastChecked: channelInfo.lastChecked || null,
            messageCount: channelInfo.messageCount || 0,
            lastMessageId: channelInfo.lastMessageId || null,
            monitoringInterval: channelInfo.monitoringInterval || 60000, // 1분
            customFilters: channelInfo.customFilters || {}
        });

        console.log(`Channel added: ${channelId} (${channelInfo.name})`);
    }

    /**
     * 카테고리 추가
     */
    addCategory(categoryId, categoryInfo) {
        this.categories.set(categoryId, {
            id: categoryId,
            name: categoryInfo.name || categoryId,
            description: categoryInfo.description || '',
            addedAt: new Date(),
            isActive: true
        });
    }

    /**
     * 채널 조회
     */
    getChannel(channelId) {
        return this.channels.get(channelId);
    }

    /**
     * 모든 채널 조회
     */
    getAllChannels() {
        return Array.from(this.channels.values());
    }

    /**
     * 카테고리별 채널 조회
     */
    getChannelsByCategory(category) {
        return this.getAllChannels().filter(channel => 
            channel.category === category && channel.isActive
        );
    }

    /**
     * 우선순위별 채널 조회
     */
    getChannelsByPriority(priority) {
        return this.getAllChannels().filter(channel => 
            channel.priority === priority && channel.isActive
        );
    }

    /**
     * 활성 채널 조회
     */
    getActiveChannels() {
        return this.getAllChannels().filter(channel => channel.isActive);
    }

    /**
     * 채널 정보 업데이트
     */
    updateChannel(channelId, updates) {
        const channel = this.channels.get(channelId);
        if (channel) {
            Object.assign(channel, updates);
            console.log(`Channel updated: ${channelId}`);
            return true;
        }
        return false;
    }

    /**
     * 채널 비활성화
     */
    deactivateChannel(channelId) {
        return this.updateChannel(channelId, { isActive: false });
    }

    /**
     * 채널 활성화
     */
    activateChannel(channelId) {
        return this.updateChannel(channelId, { isActive: true });
    }

    /**
     * 채널 삭제
     */
    removeChannel(channelId) {
        const deleted = this.channels.delete(channelId);
        if (deleted) {
            console.log(`Channel removed: ${channelId}`);
        }
        return deleted;
    }

    /**
     * 메시지 카운트 업데이트
     */
    updateMessageCount(channelId, count = 1) {
        const channel = this.channels.get(channelId);
        if (channel) {
            channel.messageCount += count;
            channel.lastChecked = new Date();
        }
    }

    /**
     * 마지막 메시지 ID 업데이트
     */
    updateLastMessageId(channelId, messageId) {
        const channel = this.channels.get(channelId);
        if (channel) {
            channel.lastMessageId = messageId;
            channel.lastChecked = new Date();
        }
    }

    /**
     * 채널 검색
     */
    searchChannels(query) {
        const lowerQuery = query.toLowerCase();
        return this.getAllChannels().filter(channel => 
            channel.name.toLowerCase().includes(lowerQuery) ||
            channel.description.toLowerCase().includes(lowerQuery) ||
            channel.keywords.some(keyword => keyword.toLowerCase().includes(lowerQuery))
        );
    }

    /**
     * 모니터링 설정 가져오기
     */
    getMonitoringSettings() {
        const activeChannels = this.getActiveChannels();
        
        const settings = {
            channels: activeChannels.map(channel => ({
                id: channel.id,
                name: channel.name,
                category: channel.category,
                priority: channel.priority,
                monitoringInterval: channel.monitoringInterval,
                keywords: channel.keywords,
                customFilters: channel.customFilters
            })),
            categories: Array.from(this.categories.values()),
            totalChannels: activeChannels.length,
            highPriorityChannels: this.getChannelsByPriority('high').length,
            mediumPriorityChannels: this.getChannelsByPriority('medium').length,
            lowPriorityChannels: this.getChannelsByPriority('low').length
        };

        return settings;
    }

    /**
     * 채널 통계 정보
     */
    getStatistics() {
        const allChannels = this.getAllChannels();
        const activeChannels = this.getActiveChannels();

        const categoryStats = {};
        const priorityStats = { high: 0, medium: 0, low: 0 };
        let totalMessages = 0;

        allChannels.forEach(channel => {
            // 카테고리 통계
            categoryStats[channel.category] = (categoryStats[channel.category] || 0) + 1;
            
            // 우선순위 통계
            if (channel.isActive) {
                priorityStats[channel.priority]++;
            }
            
            // 메시지 통계
            totalMessages += channel.messageCount;
        });

        return {
            totalChannels: allChannels.length,
            activeChannels: activeChannels.length,
            inactiveChannels: allChannels.length - activeChannels.length,
            totalMessages,
            categoryStats,
            priorityStats,
            averageMessagesPerChannel: activeChannels.length > 0 ? 
                totalMessages / activeChannels.length : 0
        };
    }

    /**
     * 채널 정보 내보내기
     */
    exportChannels(format = 'json') {
        const channels = this.getAllChannels();
        
        switch (format) {
            case 'json':
                return JSON.stringify(channels, null, 2);
            case 'csv':
                return this.generateCSV(channels);
            case 'txt':
                return this.generateTextReport(channels);
            default:
                throw new Error(`Unsupported format: ${format}`);
        }
    }

    /**
     * CSV 형식으로 변환
     */
    generateCSV(channels) {
        const headers = ['ID', 'Name', 'Category', 'Priority', 'Keywords', 'Message Count', 'Active'];
        const rows = channels.map(channel => [
            channel.id,
            channel.name,
            channel.category,
            channel.priority,
            channel.keywords.join(';'),
            channel.messageCount,
            channel.isActive ? 'Yes' : 'No'
        ]);

        return [headers, ...rows]
            .map(row => row.join(','))
            .join('\n');
    }

    /**
     * 텍스트 리포트 생성
     */
    generateTextReport(channels) {
        let report = '텔레그램 채널 관리 리포트\n';
        report += '=' .repeat(50) + '\n\n';
        
        const categories = {};
        channels.forEach(channel => {
            if (!categories[channel.category]) {
                categories[channel.category] = [];
            }
            categories[channel.category].push(channel);
        });

        Object.entries(categories).forEach(([category, categoryChannels]) => {
            report += `[${this.getCategoryName(category)}]\n`;
            report += '-'.repeat(30) + '\n';
            
            categoryChannels.forEach(channel => {
                report += `• ${channel.name} (${channel.id})\n`;
                report += `  Priority: ${channel.priority}, Messages: ${channel.messageCount}\n`;
                report += `  Keywords: ${channel.keywords.join(', ')}\n`;
                report += `  Active: ${channel.isActive ? 'Yes' : 'No'}\n\n`;
            });
        });

        return report;
    }
}

module.exports = ChannelManager;