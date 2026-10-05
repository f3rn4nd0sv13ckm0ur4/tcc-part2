import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TextInput,
  TouchableOpacity,
  FlatList,
  Modal,
  Alert,
  ActivityIndicator,
  SafeAreaView,
  StatusBar,
  ScrollView,
  RefreshControl,
  Share
} from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
// para fazer
export default function App() {
  // Configuração da API
  const [baseUrl, setBaseUrl] = useState('http://10.154.20.53:5000');
  const [showConfig, setShowConfig] = useState(false);

  // Autenticação
  const [usuarioLogado, setUsuarioLogado] = useState(null);
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [tipoLogin, setTipoLogin] = useState('usuario');

  // Estado da Aplicação
  const [abaAtiva, setAbaAtiva] = useState('estoque'); // 'estoque' | 'historico'
  const [itensEstoque, setItensEstoque] = useState([]);
  const [movimentacoes, setMovimentacoes] = useState([]);
  const [termoPesquisa, setTermoPesquisa] = useState('');
  const [filtroTipoMov, setFiltroTipoMov] = useState(''); // '' | 'ADICIONAR' | 'RETIRAR'
  const [carregando, setCarregando] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Modais de Ação
  const [modalAddVisivel, setModalAddVisivel] = useState(false);
  const [modalRetirarVisivel, setModalRetirarVisivel] = useState(false);
  const [modalCriarContaVisivel, setModalCriarContaVisivel] = useState(false);
  const [itemSelecionado, setItemSelecionado] = useState(null);

  // Formulário Adicionar Item
  const [novoNome, setNovoNome] = useState('');
  const [novaQtd, setNovaQtd] = useState('');
  const [novoResp, setNovoResp] = useState('');
  const [novoHorario, setNovoHorario] = useState('');

  // Formulário Retirar Item
  const [qtdRetirar, setQtdRetirar] = useState('');
  const [respRetirar, setRespRetirar] = useState('');

  // Formulário Criar Conta (Admin)
  const [novoUserEmail, setNovoUserEmail] = useState('');
  const [novoUserSenha, setNovoUserSenha] = useState('');
  const [novoUserTipo, setNovoUserTipo] = useState('usuario');

  useEffect(() => {
    if (usuarioLogado) {
      if (abaAtiva === 'estoque') carregarEstoque();
      if (abaAtiva === 'historico') carregarHistorico();
    }
  }, [usuarioLogado, abaAtiva, filtroTipoMov]);

  // LOGIN VIA API
  const handleLogin = async () => {
    if (!email.trim() || !senha.trim()) {
      Alert.alert('Atenção', 'Preencha o e-mail e a senha.');
      return;
    }
    setCarregando(true);
    try {
      const response = await fetch(`${baseUrl}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, senha, tipo: tipoLogin })
      });
      const data = await response.json();
      setCarregando(false);

      if (response.ok) {
        setUsuarioLogado(data.usuario);
        setNovoResp(data.usuario.email);
        setRespRetirar(data.usuario.email);
      } else {
        Alert.alert('Erro no Login', data.erro || 'Credenciais inválidas');
      }
    } catch (error) {
      setCarregando(false);
      Alert.alert('Erro de Conexão', `Não foi possível conectar ao servidor: ${baseUrl}`);
    }
  };

  const handleLogout = () => {
    setUsuarioLogado(null);
    setItensEstoque([]);
    setMovimentacoes([]);
  };

  // BUSCAR ESTOQUE VIA API
  const carregarEstoque = async () => {
    setCarregando(true);
    try {
      const response = await fetch(`${baseUrl}/api/estoque`);
      const data = await response.json();
      setCarregando(false);
      setRefreshing(false);

      if (response.ok) {
        setItensEstoque(Array.isArray(data) ? data : []);
      }
    } catch (error) {
      setCarregando(false);
      setRefreshing(false);
    }
  };

  // BUSCAR HISTÓRICO VIA API
  const carregarHistorico = async () => {
    setCarregando(true);
    try {
      let url = `${baseUrl}/api/movimentacoes`;
      if (filtroTipoMov) url += `?tipo=${filtroTipoMov}`;
      const response = await fetch(url);
      const data = await response.json();
      setCarregando(false);
      setRefreshing(false);

      if (response.ok) {
        setMovimentacoes(Array.isArray(data) ? data : []);
      }
    } catch (error) {
      setCarregando(false);
      setRefreshing(false);
    }
  };

  // ADICIONAR ITEM VIA API
  const handleAdicionarItem = async () => {
    if (!novoNome.trim() || !novaQtd.trim()) {
      Alert.alert('Atenção', 'Nome e quantidade são obrigatórios.');
      return;
    }
    setCarregando(true);
    try {
      const response = await fetch(`${baseUrl}/api/estoque`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nome: novoNome,
          quantidade: parseInt(novaQtd, 10),
          responsavel: novoResp || usuarioLogado.email,
          horario: novoHorario || new Date().toLocaleTimeString()
        })
      });
      const data = await response.json();
      setCarregando(false);

      if (response.ok) {
        Alert.alert('Sucesso', 'Item adicionado ao estoque!');
        setModalAddVisivel(false);
        setNovoNome('');
        setNovaQtd('');
        setNovoHorario('');
        carregarEstoque();
      } else {
        Alert.alert('Erro', data.erro || 'Erro ao adicionar item.');
      }
    } catch (error) {
      setCarregando(false);
      Alert.alert('Erro', 'Conexão falhou ao adicionar item.');
    }
  };

  // RETIRAR ITEM VIA API
  const handleRetirarItem = async () => {
    if (!qtdRetirar.trim() || !itemSelecionado) {
      Alert.alert('Atenção', 'Informe a quantidade a retirar.');
      return;
    }
    setCarregando(true);
    try {
      const response = await fetch(`${baseUrl}/api/estoque/${itemSelecionado.id}/retirar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          quantidade: parseInt(qtdRetirar, 10),
          responsavel: respRetirar || usuarioLogado.email
        })
      });
      const data = await response.json();
      setCarregando(false);

      if (response.ok) {
        Alert.alert('Sucesso', 'Retirada realizada com sucesso!');
        setModalRetirarVisivel(false);
        setQtdRetirar('');
        setItemSelecionado(null);
        carregarEstoque();
      } else {
        Alert.alert('Erro', data.erro || 'Erro ao realizar retirada.');
      }
    } catch (error) {
      setCarregando(false);
      Alert.alert('Erro', 'Conexão falhou ao retirar item.');
    }
  };

  // CRIAR CONTA VIA API (ADMIN)
  const handleCriarConta = async () => {
    if (!novoUserEmail.trim() || !novoUserSenha.trim()) {
      Alert.alert('Atenção', 'E-mail e senha são obrigatórios.');
      return;
    }
    setCarregando(true);
    try {
      const endpoint = novoUserTipo === 'admin' ? '/api/admin/criar_conta' : '/api/usuarios';
      const response = await fetch(`${baseUrl}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: novoUserEmail, senha: novoUserSenha })
      });
      const data = await response.json();
      setCarregando(false);

      if (response.ok) {
        Alert.alert('Sucesso', `Conta ${novoUserTipo} criada com sucesso!`);
        setModalCriarContaVisivel(false);
        setNovoUserEmail('');
        setNovoUserSenha('');
      } else {
        Alert.alert('Erro', data.erro || 'Falha ao criar conta');
      }
    } catch (error) {
      setCarregando(false);
      Alert.alert('Erro', 'Falha ao conectar com o servidor.');
    }
  };

  // RESETAR ESTOQUE (ADMIN)
  const handleResetarEstoque = () => {
    Alert.alert(
      'Confirmar Reset',
      'Deseja realmente zerar todas as quantidades do estoque?',
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Resetar',
          style: 'destructive',
          onPress: async () => {
            setCarregando(true);
            try {
              const response = await fetch(`${baseUrl}/api/admin/resetar_banco`, { method: 'POST' });
              const data = await response.json();
              setCarregando(false);
              if (response.ok) {
                Alert.alert('Sucesso', 'Estoque resetado com sucesso!');
                carregarEstoque();
              } else {
                Alert.alert('Erro', data.erro || 'Falha ao resetar estoque');
              }
            } catch (error) {
              setCarregando(false);
              Alert.alert('Erro', 'Conexão falhou ao resetar estoque.');
            }
          }
        }
      ]
    );
  };

  // EXPORTAR CSV VIA API
  const handleExportarCSV = async () => {
    try {
      const url = `${baseUrl}/api/estoque/exportar_csv`;
      await Share.share({
        title: 'Estoque CSV',
        message: `Baixar estoque em CSV: ${url}`,
        url: url
      });
    } catch (error) {
      Alert.alert('Exportar CSV', `Acesse o link no navegador: ${baseUrl}/api/estoque/exportar_csv`);
    }
  };

  // IMPORTAR CSV VIA API
  const handleImportarCSV = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['text/csv', 'text/comma-separated-values', 'application/csv', '*/*'],
        copyToCacheDirectory: true,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const fileAsset = result.assets[0];
        setCarregando(true);

        const formData = new FormData();
        formData.append('arquivo_csv', {
          uri: fileAsset.uri,
          name: fileAsset.name || 'estoque.csv',
          type: fileAsset.mimeType || 'text/csv',
        });

        const response = await fetch(`${baseUrl}/api/estoque/importar_csv`, {
          method: 'POST',
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          body: formData,
        });

        const data = await response.json();
        setCarregando(false);

        if (response.ok) {
          Alert.alert('Sucesso', data.mensagem || `CSV importado com sucesso! (${data.itens_processados} itens processados)`);
          carregarEstoque();
        } else {
          Alert.alert('Erro ao Importar', data.erro || 'Ocorreu um erro ao importar o arquivo CSV.');
        }
      }
    } catch (error) {
      setCarregando(false);
      Alert.alert('Erro', 'Falha ao selecionar ou enviar o arquivo CSV.');
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    if (abaAtiva === 'estoque') carregarEstoque();
    else carregarHistorico();
  };

  const itensFiltrados = itensEstoque.filter(item =>
    item.nome ? item.nome.toLowerCase().includes(termoPesquisa.toLowerCase()) : true
  );

  // TELA DE LOGIN
  if (!usuarioLogado) {
    return (
      <SafeAreaView style={styles.webBody}>
        <StatusBar barStyle="light-content" backgroundColor="#0056b3" />
        <ScrollView contentContainerStyle={styles.webLoginContainer}>
          
          <View style={styles.webHeaderBox}>
            <Text style={styles.webFiepBadge}>SISTEMA FIEP / SENAI</Text>
            <Text style={styles.webIconBig}>📦</Text>
            <Text style={styles.webTitleLogin}>Login</Text>
          </View>

          <View style={styles.webCardLogin}>
            <Text style={styles.webInputLabel}>E-mail</Text>
            <TextInput
              style={styles.webInput}
              placeholder="Digite seu Email"
              placeholderTextColor="#888"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
            />

            <Text style={styles.webInputLabel}>Senha</Text>
            <TextInput
              style={styles.webInput}
              placeholder="Digite sua Senha"
              placeholderTextColor="#888"
              value={senha}
              onChangeText={setSenha}
              secureTextEntry
            />

            <Text style={styles.webInputLabel}>Tipo de Acesso</Text>
            <View style={styles.webTipoSelector}>
              <TouchableOpacity
                style={[styles.webTipoBtn, tipoLogin === 'usuario' && styles.webTipoBtnActive]}
                onPress={() => setTipoLogin('usuario')}
              >
                <Text style={[styles.webTipoTxt, tipoLogin === 'usuario' && styles.webTipoTxtActive]}>Usuário</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.webTipoBtn, tipoLogin === 'admin' && styles.webTipoBtnActive]}
                onPress={() => setTipoLogin('admin')}
              >
                <Text style={[styles.webTipoTxt, tipoLogin === 'admin' && styles.webTipoTxtActive]}>Administrador</Text>
              </TouchableOpacity>
            </View>

            <TouchableOpacity style={styles.webBtnEntrar} onPress={handleLogin} disabled={carregando}>
              {carregando ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.webBtnEntrarTxt}>Entrar</Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity style={styles.btnConfig} onPress={() => setShowConfig(!showConfig)}>
              <Text style={styles.btnConfigTxt}>⚙️ Configurar IP da API ({baseUrl})</Text>
            </TouchableOpacity>

            {showConfig && (
              <View style={styles.configBox}>
                <Text style={styles.configLabel}>IP do Servidor API Flask:</Text>
                <TextInput
                  style={styles.inputConfig}
                  value={baseUrl}
                  onChangeText={setBaseUrl}
                  placeholder="http://192.168.x.x:5000"
                />
              </View>
            )}
          </View>
        </ScrollView>
      </SafeAreaView>
    );
  }

  // TELA PRINCIPAL
  return (
    <SafeAreaView style={styles.webBody}>
      <StatusBar barStyle="light-content" backgroundColor="#0056b3" />

      {/* TOPO (#0056b3) */}
      <View style={styles.webTopo}>
        <Text style={styles.webTopoTitle}>📦 Sistema de Estoque</Text>
        <Text style={styles.webTopoUser}>👤 {usuarioLogado.email}</Text>
      </View>

      <ScrollView contentContainerStyle={{ paddingBottom: 85 }} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}>
        
        {/* CONTAINER ESCURO (#003f82) */}
        <View style={styles.webContainer}>

          {/* MENU CARDS EM UMA ÚNICA LINHA */}
          <View style={styles.webMenuRow}>
            
            <TouchableOpacity
              style={[styles.webCardBtn, styles.btnAdd, abaAtiva === 'estoque' && styles.webCardBtnSelected]}
              onPress={() => { setAbaAtiva('estoque'); setModalAddVisivel(true); }}
            >
              <Text style={styles.cardBtnIcon}>➕</Text>
              <Text style={styles.cardBtnTxt} numberOfLines={1}>ADD</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.webCardBtn, styles.btnRemove]}
              onPress={() => {
                if (itensEstoque.length === 0) {
                  Alert.alert('Aviso', 'Nenhum item em estoque para retirar.');
                } else {
                  setItemSelecionado(itensEstoque[0]);
                  setModalRetirarVisivel(true);
                }
              }}
            >
      
            <TouchableOpacity
              style={[styles.webCardBtn, styles.btnHistory, abaAtiva === 'historico' && styles.webCardBtnSelected]}
              onPress={() => setAbaAtiva('historico')}
            >
              <Text style={styles.cardBtnIcon}>📋</Text>
              <Text style={styles.cardBtnTxt} numberOfLines={1}>HISTÓRICO</Text>
            </TouchableOpacity>

            {usuarioLogado.tipo === 'admin' && (
              <TouchableOpacity
                style={[styles.webCardBtn, styles.btnCreateAcc]}
                onPress={() => setModalCriarContaVisivel(true)}
              >
                <Text style={styles.cardBtnIcon}>👤</Text>
                <Text style={styles.cardBtnTxt} numberOfLines={1}>CONTA</Text>
              </TouchableOpacity>
            )}

            <TouchableOpacity style={[styles.webCardBtn, styles.btnLogout]} onPress={handleLogout}>
              <Text style={styles.cardBtnIcon}>🚪</Text>
              <Text style={styles.cardBtnTxt} numberOfLines={1}>SAIR</Text>
            </TouchableOpacity>

          </View>

          {/* ESTOQUE */}
          {abaAtiva === 'estoque' ? (
            <>
              <View style={styles.webSearchBox}>
                <TextInput
                  style={styles.webSearchInput}
                  placeholder="🔍 Pesquisar item no estoque..."
                  placeholderTextColor="#888"
                  value={termoPesquisa}
                  onChangeText={setTermoPesquisa}
                />
              </View>

              <View style={styles.webTableCard}>
                <View style={styles.webTableHeaderRow}>
                  <Text style={[styles.webTh, { flex: 2 }]}>NOME</Text>
                  <Text style={[styles.webTh, { flex: 1, textAlign: 'center' }]}>QTDE</Text>
                  <Text style={[styles.webTh, { flex: 2 }]}>RESPONSÁVEL</Text>
                  <Text style={[styles.webTh, { flex: 1.5, textAlign: 'right' }]}>HORÁRIO</Text>
                </View>

                {carregando && !refreshing && (
                  <ActivityIndicator size="large" color="#ffffff" style={{ marginVertical: 20 }} />
                )}

                {itensFiltrados.length > 0 ? (
                  itensFiltrados.map((item, index) => (
                    <TouchableOpacity
                      key={item.id ? item.id.toString() : index.toString()}
                      style={[styles.webTableRow, index % 2 === 1 && styles.webTableRowAlt]}
                      onPress={() => {
                        setItemSelecionado(item);
                        setModalRetirarVisivel(true);
                      }}
                    >
                      <Text style={[styles.webTd, styles.webTdNome, { flex: 2 }]}>{item.nome}</Text>
                      <Text style={[styles.webTd, styles.webTdQtd, { flex: 1, textAlign: 'center' }]}>{item.quantidade}</Text>
                      <Text style={[styles.webTd, { flex: 2 }]}>{item.responsavel || 'Sistema'}</Text>
                      <Text style={[styles.webTd, { flex: 1.5, textAlign: 'right', fontSize: 11 }]}>{item.horario || '-'}</Text>
                    </TouchableOpacity>
                  ))
                ) : (
                  !carregando && <Text style={styles.emptyTableTxt}>Nenhum item encontrado no estoque.</Text>
                )}
              </View>
            </>
          ) : (
            /* HISTÓRICO */
            <View style={{ marginTop: 10 }}>
              <View style={styles.filtrosRow}>
                <TouchableOpacity
                  style={[styles.filtroChip, filtroTipoMov === '' && styles.filtroChipAtivo]}
                  onPress={() => setFiltroTipoMov('')}
                >
                  <Text style={[styles.filtroTxt, filtroTipoMov === '' && styles.filtroTxtAtivo]}>Todos</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[styles.filtroChip, filtroTipoMov === 'ADICIONAR' && styles.filtroChipAtivo]}
                  onPress={() => setFiltroTipoMov('ADICIONAR')}
                >
                  <Text style={[styles.filtroTxt, filtroTipoMov === 'ADICIONAR' && styles.filtroTxtAtivo]}>Entradas</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[styles.filtroChip, filtroTipoMov === 'RETIRAR' && styles.filtroChipAtivo]}
                  onPress={() => setFiltroTipoMov('RETIRAR')}
                >
                  <Text style={[styles.filtroTxt, filtroTipoMov === 'RETIRAR' && styles.filtroTxtAtivo]}>Saídas</Text>
                </TouchableOpacity>
              </View>

              <View style={styles.webTableCard}>
                <View style={styles.webTableHeaderRow}>
                  <Text style={[styles.webTh, { flex: 2 }]}>ITEM</Text>
                  <Text style={[styles.webTh, { flex: 1, textAlign: 'center' }]}>TIPO</Text>
                  <Text style={[styles.webTh, { flex: 1, textAlign: 'center' }]}>QTD</Text>
                  <Text style={[styles.webTh, { flex: 2 }]}>RESPONSÁVEL</Text>
                </View>

                {movimentacoes.length > 0 ? (
                  movimentacoes.map((mov, index) => (
                    <View key={mov.id ? mov.id.toString() : index.toString()} style={[styles.webTableRow, index % 2 === 1 && styles.webTableRowAlt]}>
                      <Text style={[styles.webTd, styles.webTdNome, { flex: 2 }]}>{mov.item}</Text>
                      <View style={{ flex: 1, alignItems: 'center' }}>
                        <Text style={[styles.badgeTipoTxt, mov.tipo === 'ADICIONAR' ? styles.txtAdd : styles.txtRet]}>
                          {mov.tipo}
                        </Text>
                      </View>
                      <Text style={[styles.webTd, { flex: 1, textAlign: 'center', fontWeight: 'bold' }]}>{mov.quantidade}</Text>
                      <Text style={[styles.webTd, { flex: 2 }]}>{mov.responsavel}</Text>
                    </View>
                  ))
                ) : (
                  !carregando && <Text style={styles.emptyTableTxt}>Nenhuma movimentação registrada.</Text>
                )}
              </View>
            </View>
          )}

        </View>
      </ScrollView>

      {/* BARRA DE AÇÕES INFERIOR EM UMA ÚNICA LINHA (.rodape-acoes) */}
      <View style={styles.webRodapeAcoes}>
        {usuarioLogado.tipo === 'admin' && (
          <TouchableOpacity style={styles.btnResetRodape} onPress={handleResetarEstoque}>
            <Text style={styles.btnRodapeTxt} numberOfLines={1}>⚠️ Reset</Text>
          </TouchableOpacity>
        )}

        <TouchableOpacity style={styles.btnExportCsvRodape} onPress={handleExportarCSV}>
          <Text style={styles.btnRodapeTxt} numberOfLines={1}>📥 Exportar CSV</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.btnImportCsvRodape} onPress={handleImportarCSV}>
          <Text style={styles.btnRodapeTxt} numberOfLines={1}>📤 Importar CSV</Text>
        </TouchableOpacity>
      </View>

      {/* MODAL ADICIONAR ITEM */}
      <Modal visible={modalAddVisivel} animationType="fade" transparent>
        <View style={styles.modalBg}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>➕ Adicionar / Entrada de Item</Text>

            <Text style={styles.webInputLabel}>Nome do Item</Text>
            <TextInput style={styles.webInput} value={novoNome} onChangeText={setNovoNome} placeholder="Ex: Parafuso 6mm" placeholderTextColor="#888" />

            <Text style={styles.webInputLabel}>Quantidade</Text>
            <TextInput style={styles.webInput} value={novaQtd} onChangeText={setNovaQtd} keyboardType="numeric" placeholder="10" placeholderTextColor="#888" />

            <Text style={styles.webInputLabel}>Responsável</Text>
            <TextInput style={styles.webInput} value={novoResp} onChangeText={setNovoResp} />

            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.btnCancelar} onPress={() => setModalAddVisivel(false)}>
                <Text style={styles.btnCancelarTxt}>Cancelar</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.btnSalvarAdd} onPress={handleAdicionarItem}>
                <Text style={styles.btnSalvarTxt}>Salvar</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* MODAL CRIAR CONTA (ADMIN) */}
      <Modal visible={modalCriarContaVisivel} animationType="fade" transparent>
        <View style={styles.modalBg}>
          <View style={styles.modalCard}>
            <Text style={[styles.modalTitle, { color: '#27ae60' }]}>👤 Criar Nova Conta</Text>

            <Text style={styles.webInputLabel}>E-mail</Text>
            <TextInput style={styles.webInput} value={novoUserEmail} onChangeText={setNovoUserEmail} placeholder="novo.usuario@fiep.org.br" placeholderTextColor="#888" autoCapitalize="none" />

            <Text style={styles.webInputLabel}>Senha</Text>
            <TextInput style={styles.webInput} value={novoUserSenha} onChangeText={setNovoUserSenha} secureTextEntry placeholder="••••••••" placeholderTextColor="#888" />

            <Text style={styles.webInputLabel}>Tipo de Conta</Text>
            <View style={styles.webTipoSelector}>
              <TouchableOpacity
                style={[styles.webTipoBtn, novoUserTipo === 'usuario' && styles.webTipoBtnActive]}
                onPress={() => setNovoUserTipo('usuario')}
              >
                <Text style={[styles.webTipoTxt, novoUserTipo === 'usuario' && styles.webTipoTxtActive]}>Usuário</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.webTipoBtn, novoUserTipo === 'admin' && styles.webTipoBtnActive]}
                onPress={() => setNovoUserTipo('admin')}
              >
                <Text style={[styles.webTipoTxt, novoUserTipo === 'admin' && styles.webTipoTxtActive]}>Admin</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.btnCancelar} onPress={() => setModalCriarContaVisivel(false)}>
                <Text style={styles.btnCancelarTxt}>Cancelar</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.btnSalvarAdd, { backgroundColor: '#27ae60' }]} onPress={handleCriarConta}>
                <Text style={styles.btnSalvarTxt}>Criar Conta</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  webBody: { flex: 1, backgroundColor: '#dce8fa' },
  webLoginContainer: { padding: 20, justifyContent: 'center', minHeight: '100%', alignItems: 'center' },
  
  webHeaderBox: { alignItems: 'center', marginBottom: 20 },
  webFiepBadge: { color: '#0056b3', fontSize: 13, fontWeight: 'bold', letterSpacing: 1.5, marginBottom: 5 },
  webIconBig: { fontSize: 48, marginVertical: 5 },
  webTitleLogin: { fontSize: 26, fontWeight: 'bold', color: '#003f82' },

  webCardLogin: { backgroundColor: '#fff', borderRadius: 15, padding: 22, width: '100%', maxWidth: 360, elevation: 6 },
  webInputLabel: { fontSize: 13, color: '#003f82', fontWeight: 'bold', marginTop: 12, marginBottom: 4 },
  webInput: { borderWidth: 1, borderColor: '#ccc', borderRadius: 10, padding: 11, fontSize: 15, backgroundColor: '#fff', color: '#333' },

  webTipoSelector: { flexDirection: 'row', marginVertical: 8 },
  webTipoBtn: { flex: 1, padding: 10, borderRadius: 8, borderWidth: 1, borderColor: '#0056b3', alignItems: 'center', marginRight: 5 },
  webTipoBtnActive: { backgroundColor: '#0056b3' },
  webTipoTxt: { color: '#0056b3', fontWeight: 'bold', fontSize: 13 },
  webTipoTxtActive: { color: '#fff' },

  webBtnEntrar: { backgroundColor: '#0056b3', borderRadius: 10, padding: 14, alignItems: 'center', marginTop: 18, elevation: 3 },
  webBtnEntrarTxt: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  btnConfig: { marginTop: 15, alignItems: 'center' },
  btnConfigTxt: { color: '#0056b3', fontSize: 12, fontWeight: '600' },
  configBox: { marginTop: 10, padding: 10, backgroundColor: '#eef4ff', borderRadius: 8 },
  configLabel: { fontSize: 12, color: '#333', fontWeight: 'bold', marginBottom: 4 },
  inputConfig: { borderWidth: 1, borderColor: '#99c2ff', borderRadius: 6, padding: 6, backgroundColor: '#fff', fontSize: 13 },

  webTopo: { backgroundColor: '#0056b3', paddingVertical: 14, paddingHorizontal: 18, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', elevation: 4 },
  webTopoTitle: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  webTopoUser: { color: '#d0e1ff', fontSize: 12 },

  webContainer: { width: '96%', alignSelf: 'center', marginVertical: 12, backgroundColor: '#003f82', padding: 10, borderRadius: 15, elevation: 6 },

  // MENU SUPERIOR EM UMA ÚNICA LINHA
  webMenuRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  webCardBtn: { flex: 1, paddingVertical: 8, paddingHorizontal: 2, marginHorizontal: 2, borderRadius: 10, alignItems: 'center', justifyContent: 'center', elevation: 3 },
  webCardBtnSelected: { borderWidth: 2, borderColor: '#fff' },
  cardBtnIcon: { fontSize: 16 },
  cardBtnTxt: { color: '#fff', fontSize: 9, fontWeight: 'bold', marginTop: 2, textAlign: 'center' },

  btnAdd: { backgroundColor: '#0056b3' },
  btnHistory: { backgroundColor: '#f39c12' },
  btnCreateAcc: { backgroundColor: '#27ae60' },
  btnLogout: { backgroundColor: '#7f8c8d' },

  webSearchBox: { marginBottom: 12, alignItems: 'center' },
  webSearchInput: { width: '100%', backgroundColor: '#fff', borderRadius: 8, paddingHorizontal: 12, paddingVertical: 8, fontSize: 13, textAlign: 'center' },

  webTableCard: { backgroundColor: '#fff', borderRadius: 10, overflow: 'hidden' },
  webTableHeaderRow: { flexDirection: 'row', backgroundColor: '#003f82', paddingVertical: 10, paddingHorizontal: 10 },
  webTh: { color: '#fff', fontWeight: 'bold', fontSize: 11 },

  webTableRow: { flexDirection: 'row', paddingVertical: 10, paddingHorizontal: 10, borderBottomWidth: 1, borderBottomColor: '#eee', alignItems: 'center' },
  webTableRowAlt: { backgroundColor: '#f8f8f8' },
  webTd: { fontSize: 12, color: '#333' },
  webTdNome: { fontWeight: 'bold', color: '#003f82' },
  webTdQtd: { fontWeight: 'bold', color: '#0056b3' },
  emptyTableTxt: { textAlign: 'center', color: '#666', padding: 25, fontSize: 13 },

  filtrosRow: { flexDirection: 'row', marginBottom: 10, justifyContent: 'center' },
  filtroChip: { paddingVertical: 5, paddingHorizontal: 12, borderRadius: 14, backgroundColor: 'rgba(255,255,255,0.2)', marginRight: 6 },
  filtroChipAtivo: { backgroundColor: '#fff' },
  filtroTxt: { color: '#fff', fontWeight: 'bold', fontSize: 11 },
  filtroTxtAtivo: { color: '#003f82' },

  badgeTipoTxt: { fontWeight: 'bold', fontSize: 10 },
  txtAdd: { color: '#27ae60' },
  txtRet: { color: '#e03131' },

  // BARRA DE AÇÕES INFERIOR EM UMA ÚNICA LINHA
  webRodapeAcoes: { position: 'absolute', bottom: 8, left: 6, right: 6, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  btnResetRodape: { flex: 1, backgroundColor: '#ff9800', paddingVertical: 8, paddingHorizontal: 4, marginHorizontal: 2, borderRadius: 8, alignItems: 'center', elevation: 4 },
  btnExportCsvRodape: { flex: 1, backgroundColor: '#16a085', paddingVertical: 8, paddingHorizontal: 4, marginHorizontal: 2, borderRadius: 8, alignItems: 'center', elevation: 4 },
  btnImportCsvRodape: { flex: 1, backgroundColor: '#8e44ad', paddingVertical: 8, paddingHorizontal: 4, marginHorizontal: 2, borderRadius: 8, alignItems: 'center', elevation: 4 },
  btnRodapeTxt: { color: '#fff', fontWeight: 'bold', fontSize: 10, textAlign: 'center' },

  modalBg: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)', justifyContent: 'center', padding: 20 },
  modalCard: { backgroundColor: '#fff', borderRadius: 12, padding: 20 },
  modalTitle: { fontSize: 18, fontWeight: 'bold', color: '#003f82', marginBottom: 8 },
  modalSub: { fontSize: 13, color: '#555', marginBottom: 12 },
  modalActions: { flexDirection: 'row', justifyContent: 'flex-end', marginTop: 20 },
  btnCancelar: { padding: 10, marginRight: 10 },
  btnCancelarTxt: { color: '#666', fontWeight: 'bold' },
  btnSalvarAdd: { backgroundColor: '#0056b3', paddingVertical: 10, paddingHorizontal: 18, borderRadius: 6 },
  btnSalvarRet: { backgroundColor: '#e03131', paddingVertical: 10, paddingHorizontal: 18, borderRadius: 6 },
  btnSalvarTxt: { color: '#fff', fontWeight: 'bold' }
});
